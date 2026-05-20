# Задача 02. Конфигурация, роли и безопасность секретов

## Цель

Реализовать загрузку и валидацию конфигурации из `.env`, а также модель ролей Telegram-пользователей.

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
- Реализовать роли:
  - `superadmin`;
  - `admin`;
  - `viewer`.
- Если Telegram ID указан в нескольких списках, выбирать максимальную роль.
- Добавить helper для проверки прав на команды.
- Добавить маскирование секретов для логов и ошибок.

## Ожидаемые файлы

- `bot/core/config.py`
- `bot/core/security.py`
- `bot/core/roles.py`
- `.env.example`

## Критерии готовности

- Бот берет пользователей только из переменных окружения.
- Нет Telegram-команд для управления пользователями.
- Роль пользователя определяется детерминированно.
- Пароли БД и Telegram token не попадают в сообщения об ошибках.
- `.env.example` содержит все переменные из ТЗ без реальных секретов.

## Проверки

- Юнит-тесты на парсинг ролей.
- Юнит-тесты на приоритет ролей.
- Проверка, что sanitizer удаляет `WORDPRESS__DB_PASSWORD` и `TELEGRAM__BOT_TOKEN` из текста ошибки.
