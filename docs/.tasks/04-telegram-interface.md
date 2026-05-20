# Задача 04. Telegram-команды, меню и авторизация

## Цель

Реализовать Telegram-интерфейс на aiogram с русскими командами, inline-кнопками и проверкой ролей.

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
- Добавить middleware или decorator для авторизации.
- Для неавторизованных пользователей:
  - не выполнять команды;
  - отправлять короткий отказ;
  - писать событие в лог.
- Для пользователей без нужной роли:
  - не выполнять команду;
  - отправлять сообщение о недостатке прав;
  - писать событие в лог.
- Скрывать или блокировать запуск `backup`/`restore`, если уже идет тяжелая операция.

## Права доступа

- `superadmin`: все команды.
- `admin`: backup, status, disk, disk_chart, backups, clear_cache.
- `viewer`: status, disk, disk_chart, backups.

## Ожидаемые файлы

- `bot/handlers/common.py`
- `bot/handlers/backup.py`
- `bot/handlers/restore.py`
- `bot/handlers/disk.py`
- `bot/handlers/cache.py`
- `bot/keyboards/main.py`
- `bot/core/auth.py`

## Критерии готовности

- Все команды из ТЗ зарегистрированы.
- У неавторизованных пользователей нет доступа к действиям.
- Ролевые ограничения соответствуют ТЗ.
- Опасные операции используют подтверждение через inline-кнопку или отдельный confirmation flow.

## Проверки

- Тесты авторизации handlers или middleware.
- Ручная проверка через Telegram test bot.

