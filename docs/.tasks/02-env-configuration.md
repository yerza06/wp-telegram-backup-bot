# Задача 02. `.env`-конфигурация через pydantic settings

## Цель

Реализовать загрузку и валидацию конфигурации из `.env` через `pydantic-settings` без смешивания с Telegram-правами.

## Объем работ

- Реализовать `pydantic_settings` конфигурацию с `env_nested_delimiter="__"`.
- Поддержать обязательные переменные:
  - `TELEGRAM__BOT_TOKEN`;
  - `TELEGRAM__SUPERADMIN_USERS`;
  - `TELEGRAM__ADMIN_USERS`;
  - `TELEGRAM__VIEWER_USERS`;
  - `WORDPRESS__PATH`;
  - `WORDPRESS__DB_HOST`;
  - `WORDPRESS__DB_PORT`;
  - `WORDPRESS__DB_NAME`;
  - `WORDPRESS__DB_USER`;
  - `WORDPRESS__DB_PASSWORD`;
  - `BACKUP__SITE_NAME`;
  - `BACKUP__PATH_DIR`;
  - `BACKUP__TMP_PATH`;
  - `BACKUP__TIMEZONE`;
  - `BACKUP__MIN_FREE_SPACE_GB`;
  - `CORE__SQLITE_PATH`;
  - `CORE__LOGS_DIR`.
- Поддержать дополнительные переменные из ТЗ:
  - пути системных утилит;
  - `WORDPRESS__CLI_RUN_AS_USER`;
  - `BACKUP__FILE_PREFIX`;
  - `DISK_CHART__ENABLED`;
  - `DISK_CHART__FORMAT`;
  - `SCHEDULE__ENABLED`;
  - `SCHEDULE__BACKUP_CRON`.
- Добавить строгую типизацию вложенных секций:
  - `TelegramSettings`;
  - `WordPressSettings`;
  - `BackupSettings`;
  - `CoreSettings`;
  - `DiskChartSettings`;
  - `ScheduleSettings`;
  - `ToolsSettings`.
- Добавить `.env.example` со всеми переменными из ТЗ без реальных секретов.
- Добавить базовое маскирование секретов для представления конфигурации в логах и ошибках.

## Ожидаемые файлы

- `bot/core/config.py`
- `.env.example`

## Критерии готовности

- Конфигурация загружается из `.env` и переменных окружения.
- Вложенные переменные с `__` корректно парсятся.
- Ошибка отсутствующей обязательной переменной понятна разработчику.
- Пароли БД и Telegram token не попадают в сообщения об ошибках.
- `.env.example` содержит все переменные из ТЗ без реальных секретов.

## Проверки

- Юнит-тесты на загрузку обязательных и дополнительных настроек.
- Юнит-тесты на дефолтные значения.
- Проверка, что sanitizer удаляет `WORDPRESS__DB_PASSWORD` и `TELEGRAM__BOT_TOKEN` из текста ошибки.
