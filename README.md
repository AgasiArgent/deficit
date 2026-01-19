# Deficit Tracker Bot

Telegram-бот для личного трекинга показателей тела и калорий с визуализацией прогресса.

## Функционал

### Команды

- `/start` - Приветствие и список команд
- `/add` - Внести данные (интерактивный диалог)
- `/graph` - Показать график прогресса
- `/delete` - Удалить запись

### Возможности

**Ввод данных:**
- Последовательный ввод: вес → талия → шея → калории
- Валидация каждого поля
- Выбор даты (сегодня/вчера/позавчера)
- Автоматическая проверка дубликатов

**Визуализация:**
- График с 4 показателями (вес, талия, шея, калории)
- Выбор периода: неделя / месяц / 2 месяца
- Метрики прогресса (начальный → текущий)
- PNG-изображения высокого качества

**Напоминания:**
- Ежедневное напоминание в 9:00 МСК
- Настраивается через `OWNER_USER_ID`

**Удаление:**
- Показ последних 5 записей
- Подтверждение с деталями удаленных данных

## Установка

### 1. Клонировать репозиторий

```bash
cd /Users/andreynovikov/workspace/tech/internal-tools/deficit
```

### 2. Создать виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Получить токен бота

1. Открой Telegram и найди @BotFather
2. Отправь `/newbot`
3. Следуй инструкциям
4. Скопируй токен

### 5. Узнать свой User ID

1. Найди @userinfobot в Telegram
2. Отправь `/start`
3. Скопируй свой User ID

### 6. Создать .env файл

```bash
cp .env.example .env
```

Отредактируй `.env`:

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
OWNER_USER_ID=123456789
```

## Запуск

```bash
python src/main.py
```

Бот запустится и будет готов к работе. Напоминания будут приходить в 9:00 МСК.

## Использование

### Первый запуск

1. Найди своего бота в Telegram
2. Отправь `/start`
3. Используй `/add` чтобы внести первые данные

### Ежедневный workflow

1. Получи напоминание в 9:00 МСК
2. `/add` - введи данные за сегодня
3. `/graph` - посмотри прогресс

## Структура проекта

```
deficit/
├── src/
│   ├── main.py              # Точка входа
│   ├── bot/
│   │   ├── handlers.py      # Command handlers
│   │   ├── conversations.py # Conversation handler для /add
│   │   └── scheduler.py     # APScheduler для напоминаний
│   ├── database/
│   │   ├── models.py        # SQLAlchemy модели
│   │   └── queries.py       # CRUD операции
│   └── visualization/
│       └── charts.py        # Генерация matplotlib графиков
├── requirements.txt
├── .env                     # Не в git
└── deficit.db              # SQLite база (создается автоматически)
```

## Технологии

- **Python 3.11+**
- **python-telegram-bot 20.7** - Telegram Bot API
- **SQLAlchemy 2.0** - ORM для базы данных
- **SQLite** - База данных
- **matplotlib 3.8** - Генерация графиков
- **pandas 2.1** - Обработка данных
- **APScheduler 3.10** - Планирование задач
- **pytz** - Работа с часовыми поясами

## База данных

### Таблица measurements

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Primary Key |
| user_id | BIGINT | Telegram User ID |
| date | DATE | Дата замера |
| weight | FLOAT | Вес (кг) |
| waist | FLOAT | Талия (см) |
| neck | FLOAT | Шея (см) |
| calories | INTEGER | Калории |
| created_at | DATETIME | Timestamp создания |

**Уникальное ограничение:** (user_id, date) - одна запись на день.

## Troubleshooting

### Бот не отвечает

1. Проверь что токен правильный в `.env`
2. Проверь что бот запущен (`python src/main.py`)
3. Проверь логи в консоли

### Напоминания не приходят

1. Проверь что `OWNER_USER_ID` указан в `.env`
2. Проверь что user ID правильный
3. Дождись 9:00 МСК следующего дня

### График не генерируется

1. Убедись что есть хотя бы одна запись (`/add`)
2. Проверь что установлен matplotlib
3. Проверь логи на ошибки

## Development

### Автономная разработка

Проект настроен для автономной разработки через Claude Code:

```bash
# Продолжить работу над фичами
/continue-session

# Настроить для ночного режима
/setup-overnight
```

Все фичи отслеживаются в `.claude/autonomous/features.json`.

## License

MIT

## Author

Created with Claude Code (Sonnet 4.5)
