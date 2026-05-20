# Задача 03. Локальная SQLite БД

## Цель

Добавить локальную SQLite БД для метаданных бэкапов и истории операций.

## Объем работ

- Настроить SQLAlchemy ORM 2.0 с asyncio и `aiosqlite`.
- Реализовать модели:
  - `Backup`;
  - `Operation`.
- Реализовать таблицу `backups` с полями:
  - `id`;
  - `status`;
  - `created_at`;
  - `finished_at`;
  - `archive_path`;
  - `file_size_bytes`;
  - `is_removed`;
  - `error_message`.
- Реализовать таблицу `operations` с полями:
  - `id`;
  - `operation_type`;
  - `status`;
  - `started_at`;
  - `finished_at`;
  - `telegram_user_id`;
  - `backup_id`;
  - `details_json`;
  - `error_message`.
- Добавить репозитории для создания и обновления записей.
- Добавить сервис текущей тяжелой операции, который определяет, идет ли `backup` или `restore`.

## Ожидаемые файлы

- `bot/db/base.py`
- `bot/db/session.py`
- `bot/models/backup.py`
- `bot/models/operation.py`
- `bot/repositories/backups.py`
- `bot/repositories/operations.py`

## Критерии готовности

- При старте приложения создаются таблицы, если их нет.
- История операций пишется для `backup`, `restore`, `disk_check`, `cache_clear`.
- В `backups.is_removed` по умолчанию сохраняется `false`; при удалении архива через бота запись остается, а поле меняется на `true`.
- Статусы операций поддерживают `queued`, `running`, `success`, `failed`, `cancelled`.
- Сервис занятости запрещает параллельный `backup`/`restore`.

## Проверки

- Тест создания таблиц во временной SQLite БД.
- Тест создания и обновления операции.
- Тест поиска активной тяжелой операции.
