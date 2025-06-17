import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram.types import User

from utils.sessions.session_manager import session_manager

start_kb = InlineKeyboardBuilder()

session_btn = InlineKeyboardButton(
    text="Сессии",
    callback_data='sessions'
)

broadcast_btn = InlineKeyboardButton(
    text="Рассылка",
    callback_data='broadcast'
)

start_kb.add(session_btn)
start_kb.add(broadcast_btn)

def build_keyboard(data: list[list[str | int]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for text, callback in data:
        builder.button(text=text, callback_data=f'session_{callback}')

    builder.adjust(3)  # по 3 кнопки в ряд
    return builder.as_markup()

async def get_sessions_kb() -> InlineKeyboardMarkup:
    sessions = []
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            sessions.append([me.first_name, me.id])
        except Exception as e:
            logging.info(f"Ошибка: {e}")
    return build_keyboard(sessions)

def get_user_kb(user_id) -> InlineKeyboardMarkup:
    session_kb = InlineKeyboardBuilder()
    session_kb.add(InlineKeyboardButton(
        text="⏳ Среднее время ответа",
        callback_data=f'user_{user_id}'
    ))

    return session_kb.as_markup()
