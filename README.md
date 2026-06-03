# Telegram WP Backup

Локальный Telegram-бот для резервного копирования, восстановления и обслуживания одного WordPress-сайта на Ubuntu-сервере.

## Возможности

- Полный backup WordPress: `wordpress/` + `database/db.sql` + `metadata.json` в одном `.tar.zst`.
- Restore из локального бэкапа или внешнего локального архива.
- Проверка диска и PNG-график использования места.
- Очистка кэша WordPress через WP-CLI от имени `www-data` или настроенного пользователя.
- Роли Telegram-пользователей: `viewer`, `admin`, `superadmin`.
- Автоматический backup по cron-подобному расписанию через APScheduler.

## Быстрый старт локально

```bash
uv sync
cp .env.example .env
# заполните .env реальными значениями
uv run python -m bot
```

Проверки разработки:

```bash
uv run python -m compileall bot tests
uv run pytest -q
```

## Основные команды Telegram

- `/start` — меню и статус доступа.
- `/help` — справка.
- `/status` — состояние бота.
- `/disk` — свободное место на диске.
- `/disk_chart` — PNG-график диска.
- `/backup` — создать полный бэкап.
- `/backups` — список последних бэкапов.
- `/restore`, `/restore_<id>` — восстановление из локального бэкапа, только `superadmin`.
- `/restore_path <path>` — восстановление из внешнего локального `.tar.zst`, только `superadmin`.
- `/clear_cache` — очистка кэша WordPress.

## Формат бэкапа

```text
site_backup_YYYY-MM-DD_HH-mm-ss.tar.zst
├── wordpress/
├── database/
│   └── db.sql
└── metadata.json
```

## systemd

Пример unit-файла: `deploy/telegram-wp-backup.service.example`.

```bash
sudo mkdir -p /opt/telegram-wp-backup
sudo cp -r . /opt/telegram-wp-backup
cd /opt/telegram-wp-backup
uv sync
sudo cp deploy/telegram-wp-backup.service.example /etc/systemd/system/telegram-wp-backup.service
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-wp-backup.service
sudo journalctl -u telegram-wp-backup.service -f
```

## Диагностика

- Проверьте `.env` и списки Telegram ID.
- Проверьте доступность `WORDPRESS__PATH`, `BACKUP__PATH_DIR`, `BACKUP__TMP_PATH`.
- Проверьте `mysqldump`, `mysql`, `tar`, `zstd`, `df`, `du`, `wp`, `runuser`.
- Проверьте права пользователя `WORDPRESS__CLI_RUN_AS_USER`.
- Для опасных сценариев используйте staging VPS согласно `docs/testing-strategy.md`.
