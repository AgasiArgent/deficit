"""
Deficit Tracker Bot - главный файл.

Telegram-бот для отслеживания показателей тела и калорий.
"""
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from database.models import init_db
from bot.handlers import start, graph, delete
from bot.conversations import add_conversation_handler

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
        return

    # Создать приложение
    logger.info("Инициализация бота...")
    application = Application.builder().token(token).build()

    # Добавить command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(add_conversation_handler)  # Conversation для /add
    application.add_handler(CommandHandler("graph", graph))
    application.add_handler(CommandHandler("delete", delete))

    # Запустить бота
    logger.info("✅ Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    main()
