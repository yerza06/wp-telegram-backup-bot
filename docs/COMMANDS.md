# Команды и callback'и

Доступ определяется в `AccessMiddleware` (`bot/core/security.py`) на основе карт ролей из `bot/core/roles.py`. Иерархия ролей: `viewer < admin < superadmin` (старшая роль включает права младших).

## Команды

| Команда | Описание | Доступ | Файл |
|---------|----------|--------|------|
| `/start` | Приветствие, статус доступа и reply-меню | viewer | `bot/handlers/common.py` |
| `/help` | Справка по командам | viewer | `bot/handlers/common.py` |
| `/status` | Состояние бота: сайт, папка бэкапов, активная операция, свободное место | viewer | `bot/handlers/common.py` |
| `/disk` | Текстовая сводка по диску (`df`) | viewer | `bot/handlers/disk.py` |
| `/disk_chart` | PNG-график использования диска | viewer | `bot/handlers/disk.py` |
| `/backups` | Список последних бэкапов с inline-меню (открыть/восстановить/удалить) | viewer | `bot/handlers/backup.py` |
| `/backup` | Создать полный бэкап WordPress | admin | `bot/handlers/backup.py` |
| `/clear_cache` | Очистить кэш WordPress (запрос подтверждения) | admin | `bot/handlers/cache.py` |
| `/restore` | Выбрать бэкап для восстановления (список) | superadmin | `bot/handlers/restore.py` |
| `/restore_<id>` | Восстановить конкретный бэкап по id (запрос подтверждения) | superadmin | `bot/handlers/restore.py` |
| `/restore_path <path>` | Восстановить из внешнего локального `.tar.zst` (запрос подтверждения) | superadmin | `bot/handlers/restore.py` |

> `/restore_<id>` и любые команды с префиксом `restore_` требуют роли `superadmin` (правило в `command_required_role`).

## Текстовые кнопки (reply-меню)

| Кнопка | Действие | Доступ | Файл |
|--------|----------|--------|------|
| 💾 Создать полный бэкап | Аналог `/backup` | admin | `bot/handlers/backup.py` |
| 💽 Проверить диск | Аналог `/disk` | viewer | `bot/handlers/disk.py` |
| 📊 График диска | Аналог `/disk_chart` | viewer | `bot/handlers/disk.py` |
| 📦 Показать бэкапы | Аналог `/backups` | viewer | `bot/handlers/backup.py` |
| 🧹 Очистить кэш | Аналог `/clear_cache` | admin | `bot/handlers/cache.py` |

## Callback-кнопки (inline)

| Callback data | Описание | Доступ | Файл |
|---------------|----------|--------|------|
| `menu:cancel` | Отмена операции, скрытие клавиатуры | — | `bot/handlers/common.py` |
| `backup:create` | Запустить бэкап | admin | `bot/handlers/backup.py` |
| `backups:list` | Показать список бэкапов | viewer | `bot/handlers/backup.py` |
| `backup:open:<id>` | Открыть карточку бэкапа | viewer | `bot/handlers/backup.py` |
| `backup:delete:ask:<id>` | Запрос подтверждения удаления | superadmin | `bot/handlers/backup.py` |
| `backup:delete:confirm:<id>` | Подтвердить удаление бэкапа | superadmin | `bot/handlers/backup.py` |
| `disk:check` | Сводка по диску | viewer | `bot/handlers/disk.py` |
| `disk:chart` | График диска | viewer | `bot/handlers/disk.py` |
| `cache:clear:ask` | Запрос подтверждения очистки кэша | admin | `bot/handlers/cache.py` |
| `cache:clear:confirm` | Подтвердить очистку кэша | admin | `bot/handlers/cache.py` |
| `restore:select:<id>` | Выбрать бэкап для восстановления | superadmin | `bot/handlers/restore.py` |
| `restore:confirm:<id>` | Подтвердить восстановление по id | superadmin | `bot/handlers/restore.py` |
| `restore:path:confirm:<token>` | Подтвердить восстановление из внешнего архива | superadmin | `bot/handlers/restore.py` |

> Действия восстановления и удаления (`restore:*`, `backup:delete*`) доступны только `superadmin`; карточка бэкапа (`backup:open`) — от `viewer`. Правила заданы в `callback_required_role`.
