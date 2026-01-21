"""
Conversation handlers для интерактивных диалогов с пользователем.
"""
from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from sqlalchemy.exc import IntegrityError

from database.models import SessionLocal
from database.queries import create_measurement

# Состояния conversation
WEIGHT, WAIST, NECK, CALORIES, DATE_SELECTION = range(5)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало conversation для ввода данных.
    Спрашивает вес.
    """
    await update.message.reply_text(
        "📊 Начинаем ввод данных.\n\n"
        "Введи вес (кг):"
    )
    return WEIGHT


async def weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода веса.
    Валидация: положительное число.
    """
    text = update.message.text.strip()

    try:
        weight = float(text)
        if weight <= 0:
            await update.message.reply_text(
                "⚠️ Вес должен быть положительным числом.\n"
                "Попробуй снова:"
            )
            return WEIGHT

        # Сохраняем в context
        context.user_data['weight'] = weight

        await update.message.reply_text(
            f"✅ Вес: {weight} кг\n\n"
            "Введи объем талии (см):"
        )
        return WAIST

    except ValueError:
        await update.message.reply_text(
            "⚠️ Некорректный ввод. Введи число (например, 75.5).\n"
            "Попробуй снова:"
        )
        return WEIGHT


async def waist_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода объема талии.
    Валидация: положительное число или пропуск (0, -, skip).
    """
    text = update.message.text.strip().lower()

    # Проверка на пропуск
    if text in ['0', '-', 'skip', 'пропустить']:
        context.user_data['waist'] = None
        await update.message.reply_text(
            "⏭️ Талия: пропущено\n\n"
            "Введи объем шеи (см) или пропусти (0, -, skip):"
        )
        return NECK

    try:
        waist = float(text)
        if waist <= 0:
            await update.message.reply_text(
                "⚠️ Объем талии должен быть положительным числом.\n"
                "Или введи 0, - или skip чтобы пропустить.\n"
                "Попробуй снова:"
            )
            return WAIST

        # Сохраняем в context
        context.user_data['waist'] = waist

        await update.message.reply_text(
            f"✅ Талия: {waist} см\n\n"
            "Введи объем шеи (см) или пропусти (0, -, skip):"
        )
        return NECK

    except ValueError:
        await update.message.reply_text(
            "⚠️ Некорректный ввод. Введи число (например, 85.0).\n"
            "Или введи 0, - или skip чтобы пропустить.\n"
            "Попробуй снова:"
        )
        return WAIST


async def neck_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода объема шеи.
    Валидация: положительное число или пропуск (0, -, skip).
    """
    text = update.message.text.strip().lower()

    # Проверка на пропуск
    if text in ['0', '-', 'skip', 'пропустить']:
        context.user_data['neck'] = None
        await update.message.reply_text(
            "⏭️ Шея: пропущено\n\n"
            "Введи калории за вчера:"
        )
        return CALORIES

    try:
        neck = float(text)
        if neck <= 0:
            await update.message.reply_text(
                "⚠️ Объем шеи должен быть положительным числом.\n"
                "Или введи 0, - или skip чтобы пропустить.\n"
                "Попробуй снова:"
            )
            return NECK

        # Сохраняем в context
        context.user_data['neck'] = neck

        await update.message.reply_text(
            f"✅ Шея: {neck} см\n\n"
            "Введи калории за вчера:"
        )
        return CALORIES

    except ValueError:
        await update.message.reply_text(
            "⚠️ Некорректный ввод. Введи число (например, 38.5).\n"
            "Или введи 0, - или skip чтобы пропустить.\n"
            "Попробуй снова:"
        )
        return NECK


async def calories_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода калорий.
    Валидация: положительное целое число.
    Показывает кнопки выбора даты.
    """
    text = update.message.text.strip()

    try:
        calories = int(text)
        if calories <= 0:
            await update.message.reply_text(
                "⚠️ Калории должны быть положительным числом.\n"
                "Попробуй снова:"
            )
            return CALORIES

        # Сохраняем в context
        context.user_data['calories'] = calories

        # Создаем кнопки выбора даты (последние 7 дней)
        today = date.today()
        keyboard = []

        for i in range(7):
            target_date = today - timedelta(days=i)
            if i == 0:
                label = f"Сегодня ({target_date.strftime('%d.%m')})"
            elif i == 1:
                label = f"Вчера ({target_date.strftime('%d.%m')})"
            else:
                label = target_date.strftime('%d.%m.%Y')

            keyboard.append([InlineKeyboardButton(label, callback_data=f"date_{i}")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Формируем сводку с учетом пропущенных полей
        waist_str = f"{context.user_data['waist']} см" if context.user_data.get('waist') else "пропущено"
        neck_str = f"{context.user_data['neck']} см" if context.user_data.get('neck') else "пропущено"

        summary = (
            f"✅ Калории: {calories} ккал\n\n"
            f"📋 Итого:\n"
            f"• Вес: {context.user_data['weight']} кг\n"
            f"• Талия: {waist_str}\n"
            f"• Шея: {neck_str}\n"
            f"• Калории: {calories} ккал\n\n"
            f"За какой день записать?"
        )

        await update.message.reply_text(summary, reply_markup=reply_markup)
        return DATE_SELECTION

    except ValueError:
        await update.message.reply_text(
            "⚠️ Некорректный ввод. Введи целое число (например, 2200).\n"
            "Попробуй снова:"
        )
        return CALORIES


async def date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка выбора даты и сохранение в БД.
    """
    query = update.callback_query
    await query.answer()

    # Определить дату из callback_data (формат: date_N где N - количество дней назад)
    try:
        days_ago = int(query.data.split('_')[1])
        selected_date = date.today() - timedelta(days=days_ago)
    except (ValueError, IndexError):
        await query.message.reply_text("⚠️ Ошибка выбора даты. Попробуй /add снова.")
        return ConversationHandler.END

    # Получить данные из context
    user_id = update.effective_user.id
    weight = context.user_data['weight']
    waist = context.user_data.get('waist')  # Может быть None
    neck = context.user_data.get('neck')    # Может быть None
    calories = context.user_data['calories']

    # Сохранить в БД
    db = SessionLocal()
    try:
        measurement = create_measurement(
            db=db,
            user_id=user_id,
            measurement_date=selected_date,
            weight=weight,
            calories=calories,
            waist=waist,
            neck=neck
        )

        date_str = selected_date.strftime("%d.%m.%Y")
        waist_str = f"{waist} см" if waist else "пропущено"
        neck_str = f"{neck} см" if neck else "пропущено"

        success_message = (
            f"✅ Данные сохранены!\n\n"
            f"📅 Дата: {date_str}\n"
            f"• Вес: {weight} кг\n"
            f"• Талия: {waist_str}\n"
            f"• Шея: {neck_str}\n"
            f"• Калории: {calories} ккал\n\n"
            f"Используй /graph чтобы посмотреть график прогресса."
        )
        await query.message.reply_text(success_message)

    except IntegrityError:
        db.rollback()
        date_str = selected_date.strftime("%d.%m.%Y")
        await query.message.reply_text(
            f"⚠️ Запись за {date_str} уже существует!\n"
            f"Используй /delete чтобы удалить старую запись."
        )

    except Exception as e:
        db.rollback()
        await query.message.reply_text(
            f"❌ Ошибка при сохранении: {str(e)}\n"
            f"Попробуй снова с /add"
        )

    finally:
        db.close()
        # Очистить user_data
        context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отмена conversation.
    """
    await update.message.reply_text(
        "❌ Ввод данных отменен.\n"
        "Используй /add чтобы начать снова."
    )
    context.user_data.clear()
    return ConversationHandler.END


# Создать ConversationHandler
add_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('add', add_start)],
    states={
        WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_input)],
        WAIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, waist_input)],
        NECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, neck_input)],
        CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, calories_input)],
        DATE_SELECTION: [CallbackQueryHandler(date_selection, pattern='^date_')]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
