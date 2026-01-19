# Deficit Tracker Bot

Telegram-бот для отслеживания показателей тела и калорий с визуализацией прогресса.

## Функционал

- Ежедневный ввод показателей:
  - Вес (кг)
  - Объем талии (см)
  - Объем шеи (см)
  - Калории за день

- Визуализация данных на графике
- Отслеживание прогресса похудения

## Структура проекта

```
deficit/
├── src/
│   ├── bot/          # Telegram bot handlers
│   ├── database/     # Database models and queries
│   └── visualization/ # Chart generation
├── requirements.txt
└── README.md
```

## Установка

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл с токеном бота
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
```

## Запуск

```bash
python src/bot/main.py
```

## Стек

- **python-telegram-bot** - Telegram Bot API
- **SQLAlchemy** - ORM для базы данных
- **matplotlib** - Генерация графиков
- **pandas** - Обработка данных
