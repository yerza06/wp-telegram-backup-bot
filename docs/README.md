# Документация Telegram-WP-Backup

## Индекс

- `specs/technical-spec.md` — техническое задание проекта.
- `specs/technical-spec-questions.md` — вопросы и уточнения по требованиям.
- `testing-strategy.md` — стратегия безопасного тестирования локально, на staging VPS и production.
- `acceptance-checklist.md` — приемочный чеклист по ТЗ.
- `diagrams/backup-restore-flow.md` — текстовое описание схемы backup/restore.
- `diagrams/backup-restore-flow.excalidraw` — исходник диаграммы Excalidraw.
- `.tasks/00-roadmap.md` — порядок реализации проекта.
- `.tasks/` — детальные задачи по этапам реализации.

## Локальный запуск

```bash
uv sync
cp .env.example .env
uv run python -m bot
```

## Telegram-команды

- `/start`, `/help`, `/status`
- `/disk`, `/disk_chart`
- `/backup`, `/backups`
- `/restore`, `/restore_<id>`, `/restore_path <path>`
- `/clear_cache`

## Формат бэкапа

```text
*.tar.zst
├── wordpress/
├── database/
│   └── db.sql
└── metadata.json
```

## Диагностика

1. Проверить `.env` и Telegram ID пользователей.
2. Проверить доступ к `WORDPRESS__PATH`.
3. Проверить права записи в `BACKUP__PATH_DIR` и `BACKUP__TMP_PATH`.
4. Проверить `mysqldump` и `mysql`.
5. Проверить `wp` и `runuser` для очистки кэша.
6. Проверить свободное место командой `/disk`.

## Правило структуры

Проектная документация хранится в `docs/`. Спецификации, диаграммы и задачи реализации не смешиваются в корне `docs/`, а лежат в отдельных поддиректориях.
