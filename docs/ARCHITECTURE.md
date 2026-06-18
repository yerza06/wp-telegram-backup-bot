# Архитектура

Бот построен по слоистой схеме: тонкие хендлеры aiogram принимают события, делегируют работу сервисам, сервисы обращаются к данным через репозитории и запускают системные утилиты через единый раннер процессов.

## Общая схема

```
┌──────┐   сообщение/нажатие   ┌──────────────┐
│ User │ ───────────────────▶ │ Telegram API │
└──────┘                       └──────┬───────┘
                                      │ long polling
                                      ▼
                          ┌───────────────────────┐
                          │  aiogram Dispatcher    │
                          │  ┌──────────────────┐  │
                          │  │ AccessMiddleware │  │  ← проверка роли
                          │  └────────┬─────────┘  │
                          │           ▼            │
                          │      Router/Handler    │  ← bot/handlers/*
                          └───────────┬───────────-┘
                                      │ вызов метода + DI
                                      ▼
                          ┌───────────────────────┐
                          │       Services         │  ← bot/services/*
                          │  Backup / Restore /    │
                          │  Disk / Cache / ...    │
                          └─────┬───────────┬─────-┘
                                │           │
                  ┌─────────────▼──┐   ┌────▼──────────────┐
                  │ Repositories   │   │ CommandRunner     │
                  │ bot/repos/*    │   │ (subprocess)      │
                  └───────┬────────┘   └────────┬──────────┘
                          ▼                     ▼
                  ┌───────────────┐   ┌────────────────────────┐
                  │ SQLite (ORM)  │   │ tar / zstd / mysqldump  │
                  │ backups,      │   │ mysql / wp / df / du /  │
                  │ operations    │   │ cp / chown / runuser    │
                  └───────────────┘   └────────────────────────┘
```

## Слои и модули

### `bot/__main__.py` — точка входа и композиция
Создаёт все сервисы вручную (ручной DI), кладёт их в `dispatcher[...]` (workflow-data aiogram прокидывает их как именованные аргументы хендлеров), регистрирует `AccessMiddleware`, запускает планировщик и long polling. При остановке корректно гасит планировщик, сессию бота и БД.

### `bot/core/` — инфраструктура
- **config.py** — настройки на `pydantic-settings`. Вложенные группы (`telegram`, `wordpress`, `backup`, `core`, `disk_chart`, `schedule`, `tools`) читаются из `.env` с разделителем `__`. Дополнительно поддерживаются «плоские» переменные путей к утилитам, которые в `model_post_init` переносятся в `tools`. `get_settings()` кэшируется через `lru_cache`. `mask_secrets` / `sanitize_text` скрывают токен и пароль БД.
- **roles.py** — `Role(IntEnum)` (`viewer < admin < superadmin`) и карты минимально требуемых ролей для команд, callback'ов и текстовых кнопок.
- **auth.py** — `get_user_role` (по спискам ID из настроек) и `has_role`.
- **security.py** — `AccessMiddleware`: определяет требуемую роль для события, проверяет роль пользователя, кладёт `user_role` в data и блокирует доступ при нехватке прав.
- **errors.py** — иерархия доменных исключений (`BotDomainError` и наследники) с безопасными `user_message`.
- **logging.py** — ротация файла `logs/bot.log` + вывод в консоль.

### `bot/handlers/` — слой представления
Роутеры aiogram, по одному на функциональную область (`common`, `backup`, `restore`, `disk`, `cache`). Хендлеры тонкие: получают сервис через DI, вызывают его метод и отправляют результат. Собираются в один роутер в `build_router()`.

### `bot/keyboards/` — клавиатуры
Reply-меню (`main_menu_keyboard`) и inline-клавиатуры подтверждения/выбора. Здесь же константы текстов кнопок, используемые и в хендлерах, и в картах ролей.

### `bot/services/` — бизнес-логика
- **BackupService** — создание архива (копия WP в staging, дамп БД, упаковка `tar --zstd`), список/получение/удаление бэкапов, аварийный бэкап.
- **RestoreService** — восстановление по id или по внешнему пути с reserve/activate/rollback каталога WordPress и заливкой дампа в БД.
- **ArchiveService** — валидация, проверка читаемости и распаковка `.tar.zst`, проверка структуры (`wordpress/`, `database/db.sql`, `metadata.json`).
- **DiskService** / **DiskChartService** — `df`/`du`, контроль минимального свободного места, PNG-график (matplotlib).
- **CacheService** — `wp cache flush` и `wp transient delete --all` через `runuser`.
- **OperationService** — гард «одна тяжёлая операция за раз» (`OperationBusyError`).
- **BackupSchedulerService** — APScheduler с cron-триггером; откладывает плановый бэкап, если идёт другая тяжёлая операция.
- **AdminNotificationService** — рассылка сообщений админам.
- **StatusService** — текст состояния бота.
- **CommandRunner** (process.py) — единая точка запуска подпроцессов: проверка наличия утилиты, маскирование аргументов в логах, таймауты, обработка кода возврата.

### `bot/repositories/` — доступ к данным
`BackupRepository` и `OperationRepository` инкапсулируют все запросы SQLAlchemy. Сервисы не пишут SQL напрямую.

### `bot/models/` + `bot/db/`
ORM-модели `Backup` и `Operation` (SQLAlchemy 2, `Mapped`). `db/session.py` создаёт async-движок и `sessionmaker`, инициализирует схему (`create_all`) при старте.

### `bot/utils/`
`sanitize.py` — безопасное укорачивание и маскирование текста ошибок для отправки в Telegram.

## Потоки основных сценариев

### Создание бэкапа (`/backup`)
1. `AccessMiddleware` проверяет, что у пользователя роль ≥ `admin`.
2. `backup`-хендлер вызывает `BackupService.start_backup`.
3. `OperationService.ensure_no_active_heavy_operation` — гард на параллелизм.
4. В БД создаётся `Operation(running)` и `Backup(created)`.
5. `_create_archive`: проверка путей и свободного места → копия WP в staging → `mysqldump` → `metadata.json` → `tar --zstd`.
6. Запись размера/пути архива, статусы `success`; staging-каталог удаляется в `finally`.
7. Пользователю уходит путь к архиву; при ошибке — безопасный текст и запись в лог.

### Восстановление (`/restore` → выбор → подтверждение)
1. Доступ — только `superadmin`.
2. `/restore` показывает список бэкапов с существующими архивами; выбор и подтверждение через inline-кнопки.
3. `RestoreService._restore`: валидация и читаемость архива → проверка места → `reserve_directory` (текущий WP переименовывается в `*_reserve`) → распаковка во временный каталог → активация распакованного `wordpress/` → валидация установки → заливка `db.sql` в БД → `chown` на владельца → финализация (удаление reserve).
4. При любой ошибке — `rollback_reserved_directory` возвращает прежний WordPress; операция помечается `failed`.

### Новый пользователь / `/start`
1. Событие проходит через `AccessMiddleware`; для `/start` нужна роль `viewer`.
2. Если ID пользователя нет ни в одном списке (`viewer/admin/superadmin`), доступ запрещается («⛔ Доступ запрещен»).
3. Иначе бот отвечает приветствием со статусом и показывает reply-меню.

### Плановый бэкап
1. При `SCHEDULE__ENABLED=true` `BackupSchedulerService` регистрирует cron-job.
2. В момент срабатывания проверяется активная тяжёлая операция: если занято — бэкап откладывается (фоновая задача ждёт освобождения), админам уходит уведомление.
3. По завершении админам отправляется результат.

## Используемые паттерны

- **Слоистая архитектура**: handlers → services → repositories → ORM/процессы.
- **Repository** — изоляция доступа к данным от бизнес-логики.
- **Dependency Injection** — сервисы собираются в `__main__` и прокидываются через workflow-data aiogram.
- **Middleware** — централизованная авторизация (`AccessMiddleware`).
- **Single-flight / mutual exclusion** — `OperationService` не даёт запустить две тяжёлые операции.
- **Reserve / rollback** — безопасная замена каталога WordPress при восстановлении.
- **Adapter над подпроцессами** — `CommandRunner` как единственная точка запуска внешних утилит.
