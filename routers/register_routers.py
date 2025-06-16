from aiogram import Dispatcher
import routers.main
from .sessions import sessions

def register_routers(dp: Dispatcher):
    dp.include_router(routers.main.router)
    dp.include_router(sessions.router)