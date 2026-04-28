import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError

from config import BOT_TOKEN, CHANNEL_ID
from content_generator import generate_motivational_post


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
POST_INTERVAL_SECONDS = 3 * 60 * 60
RETRY_DELAY_MINUTES = 5


async def send_scheduled_post() -> None:
    post_text = generate_motivational_post()
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=post_text)
        logging.info("Post sent to channel %s", CHANNEL_ID)
        await asyncio.sleep(POST_INTERVAL_SECONDS)
    except TelegramNetworkError as error:
        logging.error("Network error while connecting to Telegram: %s", error)
        logging.info(
            "Retry scheduled in %s minutes due to network error.",
            RETRY_DELAY_MINUTES,
        )
        await asyncio.sleep(RETRY_DELAY_MINUTES * 60)
    except TelegramAPIError as error:
        logging.error("Telegram API error while sending post: %s", error)
        await asyncio.sleep(POST_INTERVAL_SECONDS)


async def main() -> None:
    logging.info("Bot started. Posts will be sent every 3 hours.")

    try:
        while True:
            await send_scheduled_post()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
