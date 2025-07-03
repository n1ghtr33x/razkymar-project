from __future__ import annotations

import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pyrogram.types import User

from .sessions.session_manager import session_manager

start_kb = InlineKeyboardBuilder()

session_btn = InlineKeyboardButton(
    text="🔗 Сессии",
    callback_data='sessions'
)

broadcast_btn = InlineKeyboardButton(
    text="💬 Рассылка",
    callback_data='broadcast'
)

stats_btn = InlineKeyboardButton(
    text='📊 Статистика',
    callback_data='stats'
)


autoresponder_btn = InlineKeyboardButton(
    text='✅ Авто-Ответчик',
    callback_data='autoresponder'
)

start_kb.add(session_btn)
start_kb.add(stats_btn)
start_kb.add(broadcast_btn)
start_kb.add(autoresponder_btn)

start_kb.adjust(1)

main_menu_broadcast = InlineKeyboardBuilder()
main_menu_broadcast_btn = InlineKeyboardButton(text='↩️ Главное меню', callback_data='broadcast_back')
main_menu_broadcast.add(main_menu_broadcast_btn)


def autoresponder_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    kb_1 = InlineKeyboardButton(
        text='📄 Изменить текст',
        callback_data='autoresponder_add_text'
    )
    kb_2 = InlineKeyboardButton(
        text='📷 Изменить фото',
        callback_data='autoresponder_add_photo'
    )
    kb_3 = InlineKeyboardButton(
        text='✅ Запустить',
        callback_data='autoresponder_run'
    )
    kb_4 = InlineKeyboardButton(
        text='❌ Отмена',
        callback_data='autoresponder_back'
    )

    builder.row(kb_1, kb_2)
    builder.row(kb_3, kb_4)

    return builder.as_markup()


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
        text='🫂 Всем',
        callback_data='broadcast_time_all'
    )

    btn_2 = InlineKeyboardButton(
        text='🔥 Последний Месяц',
        callback_data='broadcast_time_1'
    )

    btn_3 = InlineKeyboardButton(
        text='⚡️  Последние 3 месяца',
        callback_data='broadcast_time_3'
    )

    btn_4 = InlineKeyboardButton(
        text='🌙 Последние 6 месяцев',
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


async def autoresponder_users(state: FSMContext) -> InlineKeyboardMarkup:
    data = await state.get_data()
    sessions = []
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            current = data.get(f'btn_{me.id}', False)
            prefix = '✅' if current else '❌'
            sessions.append([f'{prefix} {me.first_name}', f'btn_{me.id}'])
        except Exception as e:
            logging.info(f'Ошибка: {e}')
    return autoresponder_users_build(sessions, 'autoresponder-user')


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


def autoresponder_users_build(data: list[list[str | int]], callback: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for text, user_id in data:
        builder.button(text=text, callback_data=f'{callback}_{user_id}')

    go = InlineKeyboardButton(
        text='✅ Начать',
        callback_data='autoresponder_run'
    )

    back = InlineKeyboardButton(
        text='❌ Отмена',
        callback_data='autoresponder_back'
    )

    builder.adjust(3)
    builder.row(go, back)
    return builder.as_markup()


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
    btn1 = InlineKeyboardButton(text='➕ Добавить', callback_data='add_session')
    btn2 = InlineKeyboardButton(text='➖ Удалить', callback_data='remove_session')
    builder.row(btn1, btn2)
    btn3 = InlineKeyboardButton(text='↩️ Вернуться', callback_data='back')
    builder.row(btn3)
    return builder.as_markup()


def build_phone_kb(data: list[list[str | int]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for text, callback in data:
        builder.button(text=text, callback_data=f'phone_{callback}')

    builder.adjust(2)
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


async def get_sessions_numbers() -> InlineKeyboardMarkup:
    sessions = []
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            sessions.append([me.first_name, me.phone_number])
        except Exception as e:
            logging.info(f'Ошибка: {e}')
    return build_phone_kb(sessions)


broadcast_mk = InlineKeyboardBuilder()
broadcast_all_btn = InlineKeyboardButton(
    text='🫂 Все',
    callback_data='broadcast_all'
)
broadcast_multiple_btn = InlineKeyboardButton(
    text='👥 Несколько',
    callback_data='broadcast_multiple'
)
broadcast_one_btn = InlineKeyboardButton(
    text='👤 Один',
    callback_data='broadcast_one'
)
broadcast_cancel_btn = InlineKeyboardButton(
    text='↩️ Главное меню',
    callback_data='broadcast_back'
)
broadcast_mk.row(broadcast_all_btn)
broadcast_mk.row(broadcast_multiple_btn)
broadcast_mk.row(broadcast_one_btn)
broadcast_mk.row(broadcast_cancel_btn)


def on_off_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    on = InlineKeyboardButton(
        text='✅ Включить',
        callback_data='autoresponder_on'
    )

    off = InlineKeyboardButton(
        text='🚫 Выключить',
        callback_data='autoresponder_off'
    )

    builder.add(on)
    builder.add(off)
    builder.adjust(1)

    return builder.as_markup()
