# Задача 09. Очистка кэша WordPress через WP-CLI

## Цель

Реализовать `/clear_cache`, выполняющий WP-CLI команды от имени `www-data` или пользователя из `WORDPRESS__CLI_RUN_AS_USER`.

## Объем работ

- Проверить наличие `WORDPRESS__PATH`.
- Проверить доступность `wp` или пути из `WP_CLI_PATH`.
- Выполнить команды:
  - `wp cache flush --path={WORDPRESS__PATH}`;
  - `wp transient delete --all --path={WORDPRESS__PATH}`.
- Запускать команды от имени `WORDPRESS__CLI_RUN_AS_USER` через `runuser`.
- Формировать команды только списком аргументов.
- Записать результат операции `cache_clear` в локальную БД.
- Отправить пользователю итоговое сообщение.
- Добавить подтверждение, если выбранная реализация трактует очистку кэша как опасную операцию.

## Ожидаемые файлы

- `bot/services/cache.py`
- `bot/handlers/cache.py`
- `bot/keyboards/cache.py`

## Критерии готовности

- Команда доступна ролям `admin` и `superadmin`.
- Команда недоступна `viewer`.
- WP-CLI не запускается от root напрямую, если настроен `WORDPRESS__CLI_RUN_AS_USER`.
- Ошибки `runuser`, `wp cache flush` и `wp transient delete --all` логируются.
- Telegram-сообщение не содержит длинный stderr.

## Проверки

- Тест построения argv для `runuser`.
- Тест обработки ошибки отсутствующего `wp`.
- Ручная проверка на сервере с WordPress.
