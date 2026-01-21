"""
Handlers для команд Telegram бота.
"""
from datetime import datetime, date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from database.models import SessionLocal
from database.queries import (
    get_measurements_by_period,
    get_all_measurements,
    get_last_measurements,
    delete_measurement,
    get_user_start_date,
    set_start_date
)
from visualization.charts import generate_progress_chart, format_metrics_message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler для команды /start.
    Показывает приветствие и клавиатуру с кнопками.
    """
    # Создать клавиатуру с кнопками
    keyboard = [
        [KeyboardButton("📊 Внести данные"), KeyboardButton("📈 График")],
        [KeyboardButton("📅 Дата старта"), KeyboardButton("🗑️ Удалить запись")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_message = (
        "👋 Привет! Я бот для трекинга показателей тела и калорий.\n\n"
        "Используй кнопки ниже для управления:\n\n"
        "📊 Внести данные - добавить вес, талию, шею, калории\n"
        "📈 График - посмотреть прогресс за период\n"
        "📅 Дата старта - установить дату начала трекинга\n"
        "🗑️ Удалить запись - удалить запись за день\n\n"
        "💡 Подсказки:\n"
        "• Сначала выбираешь дату, потом вводишь данные\n"
        "• Талию и шею можно пропустить (0, -, skip)\n"
        "• Можно вносить данные за последние 7 дней\n\n"
        "⏰ Каждый день в 9:00 МСК я буду напоминать тебе внести данные."
    )

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler для команды /graph.
    Показывает график с данными за выбранный период.
    """
    user_id = update.effective_user.id

    # По умолчанию показываем за месяц
    period_days = context.user_data.get('graph_period', 30)

    db = SessionLocal()
    try:
        # Получить данные
        measurements = get_measurements_by_period(db, user_id, period_days)

        if not measurements:
            await update.effective_message.reply_text(
                "📊 Нет данных для отображения.\n\n"
                "Добавь первую запись с помощью /add"
            )
            return

        # Генерировать график
        chart_buf, metrics = generate_progress_chart(measurements, period_days)

        if not chart_buf:
            await update.effective_message.reply_text(
                "❌ Ошибка при генерации графика. Попробуй позже."
            )
            return

        # Создать кнопки для выбора периода
        keyboard = [
            [
                InlineKeyboardButton("📅 Неделя", callback_data="graph_week"),
                InlineKeyboardButton("📅 Месяц", callback_data="graph_month"),
                InlineKeyboardButton("📅 2 месяца", callback_data="graph_two_months")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправить метрики
        metrics_text = format_metrics_message(metrics)

        # Отправить график
        await update.effective_message.reply_photo(
            photo=chart_buf,
            caption=metrics_text,
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.effective_message.reply_text(
            f"❌ Ошибка: {str(e)}\n"
            f"Попробуй позже или обратись к разработчику."
        )

    finally:
        db.close()


async def graph_period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback handler для смены периода графика.
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Определить период
    period_map = {
        'graph_week': 7,
        'graph_month': 30,
        'graph_two_months': 60
    }

    period_days = period_map.get(query.data, 30)
    context.user_data['graph_period'] = period_days

    db = SessionLocal()
    try:
        # Получить данные
        measurements = get_measurements_by_period(db, user_id, period_days)

        if not measurements:
            await query.message.reply_text(
                "📊 Нет данных для выбранного периода."
            )
            return

        # Генерировать график
        chart_buf, metrics = generate_progress_chart(measurements, period_days)

        if not chart_buf:
            await query.message.reply_text(
                "❌ Ошибка при генерации графика."
            )
            return

        # Создать кнопки
        keyboard = [
            [
                InlineKeyboardButton("📅 Неделя", callback_data="graph_week"),
                InlineKeyboardButton("📅 Месяц", callback_data="graph_month"),
                InlineKeyboardButton("📅 2 месяца", callback_data="graph_two_months")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправить метрики
        metrics_text = format_metrics_message(metrics)

        # Отправить новый график
        await query.message.reply_photo(
            photo=chart_buf,
            caption=metrics_text,
            reply_markup=reply_markup
        )

    except Exception as e:
        await query.message.reply_text(
            f"❌ Ошибка: {str(e)}"
        )

    finally:
        db.close()


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler для команды /delete.
    Показывает последние 5 записей для удаления.
    """
    user_id = update.effective_user.id

    db = SessionLocal()
    try:
        # Получить последние 5 записей
        measurements = get_last_measurements(db, user_id, limit=5)

        if not measurements:
            await update.message.reply_text(
                "📊 Нет записей для удаления.\n\n"
                "Добавь первую запись с помощью /add"
            )
            return

        # Создать кнопки для каждой записи
        keyboard = []
        for m in measurements:
            date_str = m.date.strftime("%d.%m.%Y")
            button_text = f"{date_str} - {m.weight}кг, {m.waist}см, {m.neck}см"
            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"delete_{m.id}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🗑️ Выбери запись для удаления:",
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка: {str(e)}"
        )

    finally:
        db.close()


async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback handler для удаления записи.
    """
    query = update.callback_query
    await query.answer()

    # Получить ID записи из callback_data
    try:
        measurement_id = int(query.data.split('_')[1])
    except (IndexError, ValueError):
        await query.message.reply_text("❌ Ошибка: некорректный ID записи.")
        return

    db = SessionLocal()
    try:
        # Получить запись для показа информации
        from database.models import Measurement
        measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()

        if not measurement:
            await query.message.reply_text("❌ Запись не найдена.")
            return

        date_str = measurement.date.strftime("%d.%m.%Y")

        # Удалить запись
        success = delete_measurement(db, measurement_id)

        if success:
            await query.message.reply_text(
                f"🗑️ Запись за {date_str} удалена.\n\n"
                f"Было:\n"
                f"• Вес: {measurement.weight} кг\n"
                f"• Талия: {measurement.waist} см\n"
                f"• Шея: {measurement.neck} см\n"
                f"• Калории: {measurement.calories} ккал"
            )
        else:
            await query.message.reply_text("❌ Не удалось удалить запись.")

    except Exception as e:
        await query.message.reply_text(
            f"❌ Ошибка при удалении: {str(e)}"
        )

    finally:
        db.close()


async def set_start_date_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler для команды /set_start.
    Устанавливает дату начала трекинга дефицита калорий.
    """
    user_id = update.effective_user.id

    # Проверить есть ли аргумент (дата)
    if context.args:
        date_str = context.args[0]
        try:
            # Парсинг даты в формате DD.MM.YYYY
            start_date = datetime.strptime(date_str, "%d.%m.%Y").date()

            # Проверка что дата не в будущем
            if start_date > date.today():
                await update.message.reply_text(
                    "⚠️ Дата не может быть в будущем.\n"
                    "Попробуй снова, например: /set_start 19.01.2026"
                )
                return

            # Сохранить дату старта
            db = SessionLocal()
            try:
                set_start_date(db, user_id, start_date)
                date_display = start_date.strftime("%d.%m.%Y")
                days_ago = (date.today() - start_date).days

                await update.message.reply_text(
                    f"✅ Дата начала трекинга установлена: {date_display}\n\n"
                    f"📊 Прошло дней: {days_ago}\n\n"
                    f"Теперь можешь вносить данные за этот период с помощью /add"
                )
            finally:
                db.close()

        except ValueError:
            await update.message.reply_text(
                "⚠️ Неправильный формат даты.\n\n"
                "Используй формат: /set_start ДД.ММ.ГГГГ\n"
                "Например: /set_start 19.01.2026"
            )
    else:
        # Показать текущую дату или предложить установить
        db = SessionLocal()
        try:
            current_start = get_user_start_date(db, user_id)

            if current_start:
                date_display = current_start.strftime("%d.%m.%Y")
                days_ago = (date.today() - current_start).days

                # Создать кнопки для изменения
                keyboard = []
                for i in range(1, 8):  # Последние 7 дней
                    suggested_date = date.today() - timedelta(days=i)
                    label = suggested_date.strftime('%d.%m.%Y')
                    keyboard.append([InlineKeyboardButton(
                        label,
                        callback_data=f"setstart_{suggested_date.strftime('%Y%m%d')}"
                    )])

                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    f"📅 Текущая дата начала: {date_display}\n"
                    f"📊 Прошло дней: {days_ago}\n\n"
                    f"Чтобы изменить, выбери дату или используй:\n"
                    f"/set_start ДД.ММ.ГГГГ",
                    reply_markup=reply_markup
                )
            else:
                # Предложить установить дату
                keyboard = []
                for i in range(1, 8):  # Последние 7 дней
                    suggested_date = date.today() - timedelta(days=i)
                    label = suggested_date.strftime('%d.%m.%Y')
                    keyboard.append([InlineKeyboardButton(
                        label,
                        callback_data=f"setstart_{suggested_date.strftime('%Y%m%d')}"
                    )])

                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    "📅 Дата начала трекинга не установлена.\n\n"
                    "Выбери дату когда начал дефицит калорий,\n"
                    "или используй: /set_start ДД.ММ.ГГГГ",
                    reply_markup=reply_markup
                )
        finally:
            db.close()


async def set_start_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback handler для установки даты старта через кнопку.
    """
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # Парсинг даты из callback_data (формат: setstart_YYYYMMDD)
    try:
        date_str = query.data.split('_')[1]
        start_date = datetime.strptime(date_str, "%Y%m%d").date()

        db = SessionLocal()
        try:
            set_start_date(db, user_id, start_date)
            date_display = start_date.strftime("%d.%m.%Y")
            days_ago = (date.today() - start_date).days

            await query.message.reply_text(
                f"✅ Дата начала трекинга установлена: {date_display}\n\n"
                f"📊 Прошло дней: {days_ago}\n\n"
                f"Теперь можешь вносить данные за этот период с помощью /add"
            )
        finally:
            db.close()

    except (ValueError, IndexError):
        await query.message.reply_text("❌ Ошибка при установке даты.")
