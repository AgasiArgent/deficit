"""
Deficit Tracker Bot - главный файл.

Telegram-бот для отслеживания показателей тела и калорий.
"""
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import BotCommand

from database.models import init_db
from bot.handlers import (
    start, graph, delete,
    graph_period_callback, delete_callback,
    set_start_date_command, set_start_date_callback
)
from bot.conversations import add_conversation_handler
from bot.keyboard import button_graph, button_start_date, button_delete
from bot.scheduler import setup_scheduler

# Загрузить переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """
    Главная функция запуска бота.
    """
    # Инициализация базы данных
    logger.info("Инициализация базы данных...")
    init_db()

    # Получить токен бота
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
        logger.error("Создай .env файл с содержимым:")
        logger.error("TELEGRAM_BOT_TOKEN=your_token_here")
        logger.error("OWNER_USER_ID=your_telegram_user_id")
        return

    # Получить user ID владельца (опционально для напоминаний)
    owner_user_id_str = os.getenv('OWNER_USER_ID')
    owner_user_id = None
    if owner_user_id_str:
        try:
            owner_user_id = int(owner_user_id_str)
        except ValueError:
            logger.warning("⚠️  OWNER_USER_ID некорректный, напоминания отключены")

    # Создать приложение
    logger.info("Инициализация бота...")
    application = Application.builder().token(token).build()

    # Добавить command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(add_conversation_handler)  # Conversation для /add (включает кнопку "📊 Внести данные")
    application.add_handler(CommandHandler("set_start", set_start_date_command))
    application.add_handler(CommandHandler("graph", graph))
    application.add_handler(CommandHandler("delete", delete))

    # Добавить handlers для кнопок клавиатуры
    application.add_handler(MessageHandler(filters.Regex("^📈 График$"), button_graph))
    application.add_handler(MessageHandler(filters.Regex("^📅 Дата старта$"), button_start_date))
    application.add_handler(MessageHandler(filters.Regex("^🗑️ Удалить запись$"), button_delete))

    # Добавить callback handlers
    application.add_handler(CallbackQueryHandler(graph_period_callback, pattern='^graph_'))
    application.add_handler(CallbackQueryHandler(delete_callback, pattern='^delete_'))
    application.add_handler(CallbackQueryHandler(set_start_date_callback, pattern='^setstart_'))

    # Настроить напоминания (если указан OWNER_USER_ID)
    if owner_user_id:
        scheduler = setup_scheduler(application.bot, owner_user_id)
        scheduler.start()
        logger.info("✅ Напоминания настроены (9:00 МСК ежедневно)")
    else:
        logger.warning("⚠️  Напоминания отключены (не указан OWNER_USER_ID в .env)")

    # Убрать bot menu button (чтобы не показывать список команд)
    async def post_init(app: Application):
        await app.bot.delete_my_commands()
        logger.info("✅ Bot menu отключен")

    application.post_init = post_init

    # Запустить бота
    logger.info("✅ Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    main()
