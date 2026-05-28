# Задача 04. Telegram-команды, меню и кнопки

## Цель

Реализовать Telegram-интерфейс на aiogram с русскими командами, меню и inline-кнопками. Ролевые ограничения подключаются отдельной задачей `05-user-access.md`.

## Объем работ

- Реализовать команды:
  - `/start`;
  - `/help`;
  - `/status`;
  - `/disk`;
  - `/disk_chart`;
  - `/backup`;
  - `/backups`;
  - `/restore`;
  - `/restore_<id>`;
  - `/restore_path <path>`;
  - `/clear_cache`.
- Реализовать inline-кнопки:
  - создать полный бэкап;
  - проверить диск;
  - показать график диска;
  - показать бэкапы;
  - очистить кэш WordPress.
- Подготовить места подключения middleware/decorator авторизации из задачи `05-user-access.md`.
- Скрывать или блокировать запуск `backup`/`restore`, если уже идет тяжелая операция.
- Все тексты команд, кнопок и сообщений писать на русском языке.

## Ожидаемые файлы

- `bot/handlers/common.py`
- `bot/handlers/backup.py`
- `bot/handlers/restore.py`
- `bot/handlers/disk.py`
- `bot/handlers/cache.py`
- `bot/keyboards/main.py`

## Критерии готовности

- Все команды из ТЗ зарегистрированы.
- Команды и кнопки возвращают русскоязычные ответы.
- Handler-слой не содержит бизнес-логику backup/restore/cache/disk напрямую.
- Опасные операции используют подтверждение через inline-кнопку или отдельный confirmation flow.

## Проверки

- Тесты регистрации handlers или smoke-тест диспетчера.
- Ручная проверка через Telegram test bot.
