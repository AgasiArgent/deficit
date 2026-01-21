"""
Обработчики для кнопок клавиатуры.
"""
from telegram import Update
from telegram.ext import ContextTypes

# Импортируем handlers
from bot.handlers import graph, delete, set_start_date_command


async def button_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Внести данные'"""
    # Имитируем команду /add
    await update.message.reply_text("Запускаю ввод данных...")
    # Вызываем add_start напрямую через conversation handler
    # Это будет обработано в main.py как команда
    pass


async def button_graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'График'"""
    await graph(update, context)


async def button_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Дата старта'"""
    await set_start_date_command(update, context)


async def button_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Удалить запись'"""
    await delete(update, context)
