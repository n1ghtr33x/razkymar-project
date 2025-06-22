from aiogram import Dispatcher
import routers.main
from .sessions import sessions
import routers.message_broadcast
from .autoresponder import main


def register_routers(dp: Dispatcher):
    dp.include_router(routers.main.router)
    dp.include_router(sessions.router)
    dp.include_router(routers.message_broadcast.router)
    dp.include_router(main.router)
