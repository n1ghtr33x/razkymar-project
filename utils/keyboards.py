import logging

from aiogram.fsm.context import FSMContext
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

def broadcast_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb_1 = InlineKeyboardButton(
        text='📄 Изменить текст',
        callback_data='broadcast_add_text'
    )
    kb_2 = InlineKeyboardButton(
        text='📷 Изменить фото',
        callback_data='broadcast_add_photo'
    )
    kb_5 = InlineKeyboardButton(
        text='⏳ Выбрать время',
        callback_data='broadcast_time'
    )
    kb_3 = InlineKeyboardButton(
        text='✅ Запустить',
        callback_data='broadcast_run'
    )
    kb_4 = InlineKeyboardButton(
        text='❌ Отмена',
        callback_data='broadcast_back'
    )
    kb.row(kb_1, kb_2)
    kb.row(kb_5)
    kb.row(kb_3, kb_4)
    return kb.as_markup()

def broadcast_time_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    btn_1 = InlineKeyboardButton(
        text='Всем',
        callback_data='broadcast_time_all'
    )

    btn_2 = InlineKeyboardButton(
        text='1 месяц',
        callback_data='broadcast_time_1'
    )

    btn_3 = InlineKeyboardButton(
        text='3 месяца',
        callback_data='broadcast_time_3'
    )

    btn_4 = InlineKeyboardButton(
        text='6 месяца',
        callback_data='broadcast_time_6'
    )

    builder.row(btn_1)
    builder.row(btn_2)
    builder.row(btn_3)
    builder.row(btn_4)

    return builder.as_markup()

async def active_users_kb() -> InlineKeyboardMarkup:
    sessions = []
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            sessions.append([me.first_name, me.id])
        except Exception as e:
            logging.info(f"Ошибка: {e}")
    return active_users_build(sessions, 'broadcast_user')

async def active_users_multiple(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    sessions = []
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            current = data.get(f'btn_{me.id}', False)
            prefix = "✅" if current else "❌"
            sessions.append([f'{prefix} {me.first_name}', f'btn_{me.id}'])
        except Exception as e:
            logging.info(f'Ошибка: {e}')
    return active_users__multiple_build(sessions, 'broadcast-user-multiple')

def active_users__multiple_build(data: list[list[str | int]], callback: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for text, user_id in data:
        builder.button(text=text, callback_data=f'{callback}_{user_id}')

    go = InlineKeyboardButton(
        text='✅ Начать',
        callback_data='broadcast_go'
    )

    back = InlineKeyboardButton(
        text='❌ Отмена',
        callback_data='broadcast_back'
    )


    builder.adjust(3)
    builder.row(go, back)
    return builder.as_markup()

def active_users_build(data: list[list[str | int]], callback: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for text, user_id in data:
        builder.button(text=text, callback_data=f'{callback}_{user_id}')

    builder.adjust(3)
    return builder.as_markup()


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

broadcast_mk = InlineKeyboardBuilder()
broadcast_all_btn = InlineKeyboardButton(
    text='Все аккаунты',
    callback_data='broadcast_all'
)
broadcast_multiple_btn = InlineKeyboardButton(
    text='Несколько аккаунтов',
    callback_data='broadcast_multiple'
)
broadcast_one_btn = InlineKeyboardButton(
    text='Один аккаунт',
    callback_data='broadcast_one'
)
broadcast_cancel_btn = InlineKeyboardButton(
    text='❌ Назад',
    callback_data='broadcast_back'
)
broadcast_mk.row(broadcast_all_btn)
broadcast_mk.row(broadcast_multiple_btn)
broadcast_mk.row(broadcast_one_btn)
broadcast_mk.row(broadcast_cancel_btn)
