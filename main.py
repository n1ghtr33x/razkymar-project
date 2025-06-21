import asyncio
import logging

from aiogram import Bot, Dispatcher
from routers.register_routers import register_routers

from config import bot_token
from utils.sessions.session_manager import session_manager


async def on_startup():
    await session_manager.load_sessions()
    await session_manager.load_second_sessions()

async def on_shutdown():
    await session_manager.stop_all_sessions()

async def main():
    bot = Bot(token='7971769690:AAE_8kcIwPF7sXJ2quEDyrRCPNWk8P4LMC0')
    dp = Dispatcher()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    register_routers(dp)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Остановка...")