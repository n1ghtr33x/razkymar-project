from aiogram import Bot, Dispatcher
from config import bot_token

bot = Bot(token=bot_token)
dp = Dispatcher()

async def start_aiogram():
    await dp.start_polling()