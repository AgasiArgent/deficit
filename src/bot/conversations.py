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
from database.queries import create_measurement, update_or_create_calories

# Состояния conversation
WEIGHT, WAIST, NECK, CALORIES, DATE_SELECTION = range(5)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало conversation для ввода данных.
    Сначала спрашивает дату (или автоматически выбирает сегодня если из напоминания).
    """
    # Проверить есть ли параметр auto_date (из напоминания)
    if context.args and context.args[0] == 'auto':
        # Автоматически выбираем сегодня
        context.user_data['selected_date'] = date.today()
        await update.message.reply_text(
            f"📊 Вношу данные за сегодня ({date.today().strftime('%d.%m.%Y')})\n\n"
            "Введи вес (кг):"
        )
        return WEIGHT

    # Иначе спрашиваем дату
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

        keyboard.append([InlineKeyboardButton(label, callback_data=f"selectdate_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📅 За какой день вносишь данные?",
        reply_markup=reply_markup
    )
    return DATE_SELECTION


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

        # Вычислить дату для калорий (день назад от selected_date)
        selected_date = context.user_data['selected_date']
        calories_date = selected_date - timedelta(days=1)
        calories_date_str = calories_date.strftime('%d.%m.%Y')

        await update.message.reply_text(
            f"⏭️ Шея: пропущено\n\n"
            f"Введи калории за {calories_date_str}:"
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

        # Вычислить дату для калорий (день назад от selected_date)
        selected_date = context.user_data['selected_date']
        calories_date = selected_date - timedelta(days=1)
        calories_date_str = calories_date.strftime('%d.%m.%Y')

        await update.message.reply_text(
            f"✅ Шея: {neck} см\n\n"
            f"Введи калории за {calories_date_str}:"
        )
        return CALORIES

    except ValueError:
        await update.message.reply_text(
            "⚠️ Некорректный ввод. Введи число (например, 38.5).\n"
            "Или введи 0, - или skip чтобы пропустить.\n"
            "Попробуй снова:"
        )
        return NECK


async def date_selection_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка выбора даты в начале conversation.
    После выбора даты переходим к вводу веса.
    """
    query = update.callback_query
    await query.answer()

    # Определить дату из callback_data (формат: selectdate_N где N - количество дней назад)
    try:
        days_ago = int(query.data.split('_')[1])
        selected_date = date.today() - timedelta(days=days_ago)

        # Сохраняем дату в context
        context.user_data['selected_date'] = selected_date

        date_str = selected_date.strftime('%d.%m.%Y')
        await query.message.reply_text(
            f"📅 Вношу данные за {date_str}\n\n"
            "Введи вес (кг):"
        )
        return WEIGHT

    except (ValueError, IndexError):
        await query.message.reply_text("⚠️ Ошибка выбора даты. Попробуй /add снова.")
        return ConversationHandler.END


async def calories_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка ввода калорий.
    Валидация: положительное целое число.
    Сохраняет все данные в БД.
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

        # Получить все данные
        user_id = update.effective_user.id
        selected_date = context.user_data['selected_date']
        weight = context.user_data['weight']
        waist = context.user_data.get('waist')
        neck = context.user_data.get('neck')

        # Вычислить дату для калорий (день назад)
        calories_date = selected_date - timedelta(days=1)

        # Сохранить в БД
        db = SessionLocal()
        try:
            # 1. Создать запись за selected_date с весом/талией/шеей (БЕЗ калорий)
            measurement = create_measurement(
                db=db,
                user_id=user_id,
                measurement_date=selected_date,
                weight=weight,
                waist=waist,
                neck=neck,
                calories=None  # Калории сохраняются отдельно за предыдущий день
            )

            # 2. Сохранить/обновить калории за предыдущий день
            calories_measurement = update_or_create_calories(
                db=db,
                user_id=user_id,
                measurement_date=calories_date,
                calories=calories
            )

            date_str = selected_date.strftime("%d.%m.%Y")
            calories_date_str = calories_date.strftime("%d.%m.%Y")
            waist_str = f"{waist} см" if waist else "пропущено"
            neck_str = f"{neck} см" if neck else "пропущено"

            success_message = (
                f"✅ Данные сохранены!\n\n"
                f"📅 За {date_str}:\n"
                f"• Вес: {weight} кг\n"
                f"• Талия: {waist_str}\n"
                f"• Шея: {neck_str}\n\n"
                f"📅 За {calories_date_str}:\n"
                f"• Калории: {calories} ккал\n\n"
                f"Используй кнопки ниже для следующих действий."
            )
            await update.message.reply_text(success_message)

        except IntegrityError:
            db.rollback()
            date_str = selected_date.strftime("%d.%m.%Y")
            await update.message.reply_text(
                f"⚠️ Запись за {date_str} уже существует!\n"
                f"Используй кнопку 🗑️ Удалить запись чтобы удалить старую."
            )

        except Exception as e:
            db.rollback()
            await update.message.reply_text(
                f"❌ Ошибка при сохранении: {str(e)}\n"
                f"Попробуй снова с кнопки 📊 Внести данные"
            )

        finally:
            db.close()
            # Очистить user_data
            context.user_data.clear()

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "⚠️ Некорректный ввод. Введи целое число (например, 2200).\n"
            "Попробуй снова:"
        )
        return CALORIES




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
    entry_points=[
        CommandHandler('add', add_start),
        MessageHandler(filters.Regex("^📊 Внести данные$"), add_start)
    ],
    states={
        DATE_SELECTION: [CallbackQueryHandler(date_selection_start, pattern='^selectdate_')],
        WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_input)],
        WAIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, waist_input)],
        NECK: [MessageHandler(filters.TEXT & ~filters.COMMAND, neck_input)],
        CALORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, calories_input)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
