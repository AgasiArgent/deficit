"""
Scheduler для автоматических напоминаний.
"""
import logging
import pytz
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

logger = logging.getLogger(__name__)

# Часовой пояс Москвы
MOSCOW_TZ = pytz.timezone('Europe/Moscow')


async def send_daily_reminder(bot: Bot, user_id: int):
    """
    Отправить ежедневное напоминание пользователю.

    Args:
        bot: Telegram Bot instance
        user_id: ID пользователя
    """
    try:
        message = (
            "⏰ Доброе утро! Пора внести данные за сегодня.\n\n"
            "Используй /add чтобы записать:\n"
            "• Вес (кг)\n"
            "• Объем талии (см)\n"
            "• Объем шеи (см)\n"
            "• Калории за вчера"
        )

        await bot.send_message(chat_id=user_id, text=message)
        logger.info(f"Daily reminder sent to user {user_id}")

    except Exception as e:
        logger.error(f"Failed to send reminder to user {user_id}: {e}")


def setup_scheduler(bot: Bot, user_id: int) -> AsyncIOScheduler:
    """
    Настроить и запустить scheduler для напоминаний.

    Args:
        bot: Telegram Bot instance
        user_id: ID пользователя для отправки напоминаний

    Returns:
        AsyncIOScheduler instance
    """
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)

    # Добавить job для ежедневного напоминания в 9:00 МСК
    scheduler.add_job(
        send_daily_reminder,
        trigger=CronTrigger(hour=9, minute=0, timezone=MOSCOW_TZ),
        args=[bot, user_id],
        id='daily_reminder',
        name='Daily measurement reminder',
        replace_existing=True
    )

    logger.info(f"Scheduler configured: Daily reminder at 9:00 MSK for user {user_id}")

    return scheduler
