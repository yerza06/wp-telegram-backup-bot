# Деплой

В репозитории есть готовый способ деплоя — **systemd** (пример юнита `deploy/wp-telegram-backup-bot.service.example`). Dockerfile и docker-compose в проекте отсутствуют.

## Требования

- Linux-сервер с Python 3.13+.
- Установленный [`uv`](https://docs.astral.sh/uv/) (рекомендуется) или `pip`.
- Системные утилиты: `tar`, `zstd`, `mysqldump`, `mysql`, `df`, `du`, `cp`, `chown`, `runuser`, при использовании очистки кэша — `wp` (WP-CLI).
- Доступ к БД WordPress и права на чтение/запись каталога сайта.

## Установка через systemd

1. Скопируйте проект в рабочий каталог (юнит по умолчанию ожидает `/opt/wp-telegram-backup-bot`):

   ```bash
   sudo mkdir -p /opt/wp-telegram-backup-bot
   sudo cp -r . /opt/wp-telegram-backup-bot
   cd /opt/wp-telegram-backup-bot
   ```

2. Установите зависимости в виртуальное окружение `.venv` (на него ссылается `ExecStart` юнита):

   ```bash
   uv sync
   ```

3. Подготовьте `.env` и ограничьте права (внутри токен бота и пароль БД):

   ```bash
   cp .env.example .env
   sudo nano .env
   sudo chown root:root .env && sudo chmod 600 .env
   ```

4. Установите и запустите сервис:

   ```bash
   sudo cp deploy/wp-telegram-backup-bot.service.example /etc/systemd/system/wp-telegram-backup-bot.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now wp-telegram-backup-bot.service
   ```

5. Проверьте логи:

   ```bash
   sudo journalctl -u wp-telegram-backup-bot.service -f
   ```

## Что задаёт юнит

- `ExecStart=/opt/wp-telegram-backup-bot/.venv/bin/python -m bot` — запуск бота.
- `EnvironmentFile=/opt/wp-telegram-backup-bot/.env` — переменные окружения.
- `Wants/After=mariadb.service` — бот стартует после БД, но её недоступность не роняет сервис целиком.
- `Restart=on-failure`, `StartLimitBurst=5` — перезапуск с защитой от crash-loop.
- `UMask=0027` — архивы и дампы недоступны «прочим» пользователям.
- `TimeoutStopSec=120`, `KillMode=mixed` — долгие бэкапы/restore не убиваются мгновенно при остановке.
- `CPUQuota=100%` — ограничение нагрузки от компрессии zstd (подстраивается под сервер).
- Логи — в journald (`SyslogIdentifier=wp-telegram-backup-bot`).

> Юнит запускается от `root` (нужно для `chown` и `runuser` при восстановлении). Если меняете рабочий каталог, синхронно поправьте `WorkingDirectory`, `EnvironmentFile` и `ExecStart`.

## Запуск без systemd (например, для проверки)

```bash
uv sync
cp .env.example .env   # заполнить значения
uv run python -m bot
```

> Опасные сценарии (восстановление) рекомендуется проверять на staging-сервере — см. `docs/testing-strategy.md`.
