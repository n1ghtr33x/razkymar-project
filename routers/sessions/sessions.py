import asyncio

from aiogram import Router, types, F
from aiogram.types import FSInputFile
from pyrogram.types import User

from utils.keyboards import get_sessions_kb, get_user_kb
from utils.sessions.add_userbots import start_pyrogram
from utils.sessions.session_manager import session_manager
from utils.scripts import get_average_response_time

router = Router()

@router.callback_query(F.data == 'sessions')
async def sessions(call: types.CallbackQuery):
    await call.message.edit_text('Сессии:')
    await call.message.edit_reply_markup(call.inline_message_id, await get_sessions_kb())

@router.callback_query(F.data.startswith("session_"))
async def accounts(call: types.CallbackQuery):
    data = call.data.split('_')

    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            if me.id == int(data[1]):
                await call.message.edit_text(f'🛠 Управление сессией: {me.first_name}')
                await call.message.edit_reply_markup(call.inline_message_id, get_user_kb(me.id))
        except Exception as e:
            await call.message.edit_text(f"❌ Ошибка сессии: {str(e)}\n\n")

@router.callback_query(F.data.startswith("user_"))
async def average_time(call: types.CallbackQuery):
    await call.message.delete()
    data = call.data.split('_')
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            if me.id == int(data[1]):
                mess = await call.message.answer('Загрузка среднего время ответа...')
                avg_text = await get_average_response_time(client)
                await mess.edit_text(f'Среднее время ответа {avg_text}')
            asyncio.create_task(start_pyrogram(f'{me.phone_number}', await client.export_session_string()))
        except Exception as e:
            await call.message.answer(f"❌ Ошибка сессии: {str(e)}\n\n")