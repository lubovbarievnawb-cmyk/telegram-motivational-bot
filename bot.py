import os
import random
import requests
import asyncio
import logging
from datetime import datetime, time, timedelta

from dotenv import load_dotenv
load_dotenv()

print("BOT_TOKEN =", os.getenv('BOT_TOKEN'))
print("CHANNEL_ID =", os.getenv('CHANNEL_ID'))
print("UNSPLASH_ACCESS_KEY =", os.getenv('UNSPLASH_ACCESS_KEY'))

from telegram import Bot
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("BOT_TOKEN и CHANNEL_ID должны быть установлены!")

# Темы для картинок Unsplash
THEMES = ['meditation', 'nature', 'peace', 'spirituality', 'zen', 'mindfulness', 'tranquility']


def get_random_image():
    """Получить случайную картинку с Unsplash"""
    if not UNSPLASH_ACCESS_KEY:
        logger.warning("UNSPLASH_ACCESS_KEY не установлен, картинки не будут добавляться")
        return None

    try:
        theme = random.choice(THEMES)
        url = "https://api.unsplash.com/photos/random"
        params = {
            'query': theme,
            'orientation': 'portrait',
            'client_id': UNSPLASH_ACCESS_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        image_url = data['urls']['regular']

        logger.info(f"Получена картинка по теме: {theme}")
        return image_url

    except Exception as e:
        logger.error(f"Ошибка при получении картинки: {e}")
        return None


def load_posts(filename):
    """Загрузить посты из файла как блоки, разделённые пустой строкой"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            logger.error(f"Файл {filename} пустой")
            return []

        # Разделяем по двум переводам строки: один пост = один блок
        raw_posts = content.split('\n\n')
        posts = [p.strip() for p in raw_posts if p.strip()]

        logger.info(f"Загружено {len(posts)} постов из {filename}")
        return posts

    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден!")
        return []


async def post_from_file(filename, slot_name):
    """Опубликовать случайный пост из указанного файла с картинкой"""
    try:
        bot = Bot(token=BOT_TOKEN)
        posts = load_posts(filename)

        if not posts:
            logger.error(f"Нет доступных постов для {slot_name} из файла {filename}")
            return

        post_text = random.choice(posts)
        image_url = get_random_image()

        if image_url:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=image_url,
                caption=post_text
            )
            logger.info(f"[{slot_name}] Пост с картинкой опубликован")
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=post_text
            )
            logger.info(f"[{slot_name}] Текстовый пост опубликован")

    except TelegramError as e:
        logger.error(f"Ошибка Telegram при постинге {slot_name}: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при постинге {slot_name}: {e}")


async def post_morning():
    await post_from_file('morning.txt', 'Утро')


async def post_day():
    await post_from_file('day.txt', 'День')


async def post_evening():
    await post_from_file('evening.txt', 'Вечер')


def seconds_until(target_time: time) -> float:
    """Сколько секунд до следующего наступления заданного времени (локального)"""
    now = datetime.now()
    today_target = datetime.combine(now.date(), target_time)

    if today_target <= now:
        today_target += timedelta(days=1)

    delta = today_target - now
    return delta.total_seconds()


async def scheduler():
    """Простой планировщик: ждёт до нужного времени и запускает постинг"""
    logger.info("Планировщик запущен")

    while True:
        now = datetime.now().time()

        # Времена постов (локальное время сервера)
        morning_time = time(7, 0)   # 07:00
        day_time = time(13, 0)      # 13:00
        evening_time = time(20, 0)  # 20:00

        # Определяем, какое событие следующее
        candidates = [
            ('morning', morning_time),
            ('day', day_time),
            ('evening', evening_time),
        ]

        # Считаем время до каждого слота
        times_to_slots = [
            (name, seconds_until(t))
            for name, t in candidates
        ]

        # Берём ближайший слот
        next_slot, wait_seconds = min(times_to_slots, key=lambda x: x[1])

        logger.info(f"Следующий слот: {next_slot}, через {int(wait_seconds)} секунд")
        await asyncio.sleep(wait_seconds)

        if next_slot == 'morning':
            await post_morning()
        elif next_slot == 'day':
            await post_day()
        elif next_slot == 'evening':
            await post_evening()


async def main():
    logger.info("Бот запущен")
    logger.info(f"Канал: {CHANNEL_ID}")

    # Можно сразу ничего не постить, а ждать ближайшего слота
    await scheduler()


if __name__ == '__main__':
    asyncio.run(main())
