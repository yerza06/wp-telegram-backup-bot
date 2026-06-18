# Telegram WP Backup

Локальный Telegram-бот для резервного копирования, восстановления и обслуживания одного WordPress-сайта на Linux-сервере. Бот запускает системные утилиты (`tar`, `zstd`, `mysqldump`, `mysql`, `wp-cli`) от своего имени, хранит историю операций в локальной SQLite и управляется через Telegram с ролевым доступом.

![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.28-blue)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![Status](https://img.shields.io/badge/status-active-brightgreen)

## Features

- **Полный бэкап WordPress** — каталог сайта + дамп БД (`mysqldump`) + `metadata.json` упаковываются в один `.tar.zst`.
- **Восстановление** из локального бэкапа (`/restore`, `/restore_<id>`) или из внешнего локального архива (`/restore_path`) с reserve/rollback-механизмом.
- **Инлайн-меню бэкапов** (`/backups`) — просмотр, восстановление и безвозвратное удаление выбранного бэкапа.
- **Контроль диска** (`/disk`) и **PNG-график использования места** (`/disk_chart`) на основе matplotlib.
- **Очистка кэша WordPress** (`/clear_cache`) через WP-CLI от имени `www-data` или настроенного пользователя.
- **Ролевой доступ**: `viewer`, `admin`, `superadmin` — права проверяются в middleware.
- **Плановый бэкап по расписанию** (cron-выражение) через APScheduler с уведомлением админов.
- **Защита от параллельных тяжёлых операций** — одновременно выполняется только один бэкап/restore.
- **Маскирование секретов** в логах и сообщениях об ошибках (токен бота, пароль БД).

## Tech Stack

| Слой | Технология |
|------|-----------|
| Telegram Bot API | [aiogram](https://docs.aiogram.dev/) 3.28 (long polling) |
| Конфигурация | pydantic-settings 2 (вложенные настройки через `__`) |
| База данных | SQLite через SQLAlchemy 2 (async) + aiosqlite |
| Планировщик | APScheduler 3 (`AsyncIOScheduler`, `CronTrigger`) |
| Графики | matplotlib (бэкенд `Agg`) |
| Системные утилиты | `tar`, `zstd`, `mysqldump`, `mysql`, `wp-cli`, `df`, `du`, `cp`, `chown`, `runuser` |
| Тесты | pytest, pytest-asyncio |
| Python | 3.13+ |

## Quick Start

```bash
git clone git@github.com:yerza06/wp-telegram-backup-bot.git
cd wp-telegram-backup-bot
cp .env.example .env
# отредактируйте .env: токен бота, ID пользователей, путь к WordPress, доступ к БД

# вариант с uv (рекомендуется, в проекте есть uv.lock)
uv sync
uv run python -m bot

# либо через pip
pip install -r requirements.txt
python -m bot
```

Проверки при разработке:

```bash
uv run python -m compileall bot tests
uv run pytest -q
```

## Project Structure

```
.
├── bot/
│   ├── __main__.py          # точка входа: сборка сервисов, DI, запуск polling
│   ├── core/                # инфраструктура
│   │   ├── config.py        #   настройки (pydantic-settings) и маскирование секретов
│   │   ├── roles.py         #   роли и карты минимально требуемых прав
│   │   ├── auth.py          #   определение роли пользователя
│   │   ├── security.py      #   AccessMiddleware — проверка доступа
│   │   ├── errors.py        #   доменные исключения
│   │   └── logging.py       #   настройка логирования (ротация файла + консоль)
│   ├── handlers/            # роутеры aiogram (команды, кнопки, callback)
│   │   ├── common.py        #   /start, /help, /status, отмена
│   │   ├── backup.py        #   /backup, /backups, меню действий с бэкапом
│   │   ├── restore.py       #   /restore, /restore_<id>, /restore_path
│   │   ├── disk.py          #   /disk, /disk_chart
│   │   └── cache.py         #   /clear_cache
│   ├── keyboards/           # reply- и inline-клавиатуры
│   ├── services/            # бизнес-логика (backup, restore, archive, disk,
│   │                        #   cache, scheduler, operations, notifications, …)
│   ├── repositories/        # доступ к данным (backups, operations)
│   ├── models/              # ORM-модели SQLAlchemy (Backup, Operation)
│   ├── db/                  # движок, sessionmaker, инициализация схемы
│   └── utils/               # вспомогательные функции (sanitize)
├── deploy/                  # пример systemd-юнита
├── docs/                    # документация (архитектура, команды, конфиг, деплой)
├── tests/                   # тесты pytest
├── pyproject.toml           # зависимости и метаданные проекта
├── requirements.txt         # зафиксированные зависимости
└── .env.example             # шаблон переменных окружения
```

## Формат бэкапа

```text
<site>_backup_YYYY-MM-DD_HH-MM-SS.tar.zst
├── wordpress/        # копия каталога WordPress
├── database/
│   └── db.sql        # дамп БД (mysqldump --single-transaction)
└── metadata.json     # имя сайта, дата, id операции/бэкапа, формат
```

## Configuration

Все настройки задаются через `.env` (формат pydantic-settings, вложенность через `__`). Ключевые переменные:

| Переменная | Обязательно | Описание |
|------------|-------------|----------|
| `TELEGRAM__BOT_TOKEN` | ✅ | Токен Telegram-бота |
| `TELEGRAM__SUPERADMIN_USERS` | — | ID пользователей с правами `superadmin` |
| `WORDPRESS__PATH` | ✅ | Путь к каталогу WordPress |
| `WORDPRESS__DB_NAME` / `DB_USER` / `DB_PASSWORD` | ✅ | Доступ к БД сайта |
| `BACKUP__SITE_NAME` | ✅ | Имя сайта (используется в имени архива) |
| `BACKUP__PATH_DIR` | ✅ | Каталог хранения бэкапов |
| `SCHEDULE__ENABLED` / `SCHEDULE__BACKUP_CRON` | — | Плановый бэкап по расписанию |

Полный список — в [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Deployment

Деплой выполняется через systemd (в репозитории есть пример юнита `deploy/wp-telegram-backup-bot.service.example`). Подробная инструкция — в [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Документация

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — архитектура и потоки данных
- [docs/COMMANDS.md](docs/COMMANDS.md) — все команды и callback'и
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) — переменные окружения
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — установка и запуск
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — история изменений
