# Задача 01. Каркас проекта и зависимости

## Цель

Подготовить Python-проект к реализации Telegram-бота по ТЗ: зависимости, структура модулей, точка входа, базовая инициализация приложения.

## Объем работ

- Обновить `pyproject.toml`:
  - `aiogram`;
  - `pydantic-settings`;
  - `SQLAlchemy` с asyncio;
  - `aiosqlite`;
  - `APScheduler`;
  - `matplotlib`;
  - `numpy`;
  - `pandas`;
  - зависимости для тестов, если будут добавлены.
- Привести `bot/__main__.py` к рабочей точке входа.
- Создать модульную структуру:
  - `bot/core/`;
  - `bot/db/`;
  - `bot/models/`;
  - `bot/repositories/`;
  - `bot/services/`;
  - `bot/handlers/`;
  - `bot/keyboards/`;
  - `bot/utils/`.
- Удалить или заменить шаблонные сущности, не относящиеся к ТЗ, например текущую PostgreSQL/Redis-заготовку.
- Добавить минимальный lifecycle приложения:
  - загрузка конфигурации;
  - инициализация логирования;
  - инициализация БД;
  - старт aiogram polling.

## Ожидаемые файлы

- `pyproject.toml`
- `bot/__main__.py`
- `bot/core/config.py`
- `bot/core/logging.py`
- `bot/db/session.py`
- `bot/handlers/__init__.py`
- `bot/services/__init__.py`

## Критерии готовности

- Проект устанавливается и запускается командой из README.
- Импорт `bot` не падает из-за несуществующих классов или шаблонного кода.
- Приложение может стартовать до подключения конкретных Telegram handlers.
- Версия Python соответствует `>=3.13`.

## Проверки

- `python -m bot`
- `python -m compileall bot`

