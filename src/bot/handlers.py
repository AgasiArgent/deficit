"""
Handlers для команд Telegram бота.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database.models import SessionLocal
from database.queries import (
    get_measurements_by_period,
    get_all_measurements,
    get_last_measurements,
    delete_measurement
)
from visualization.charts import generate_progress_chart, format_metrics_message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler для команды /start.
    Показывает приветствие и список доступных команд.
    """
    welcome_message = (
        "👋 Привет! Я бот для трекинга показателей тела и калорий.\n\n"
        "📊 Доступные команды:\n\n"
        "/add - Внести данные (вес, талия, шея, калории)\n"
        "/graph - Показать график прогресса\n"
        "/delete - Удалить запись\n\n"
        "⏰ Каждый день в 9:00 МСК я буду напоминать тебе внести данные.\n\n"
        "Начни с команды /add чтобы внести первые показатели!"
    )

    await update.message.reply_text(welcome_message)


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
            await update.message.reply_text(
                "📊 Нет данных для отображения.\n\n"
                "Добавь первую запись с помощью /add"
            )
            return

        # Генерировать график
        chart_buf, metrics = generate_progress_chart(measurements, period_days)

        if not chart_buf:
            await update.message.reply_text(
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
        await update.message.reply_photo(
            photo=chart_buf,
            caption=metrics_text,
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(
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
