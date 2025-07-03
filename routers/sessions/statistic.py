from aiogram import Router, types, F, Bot
from pyrogram.types import User

from utils.keyboards import start_kb
from utils.scripts import get_average_response_time
from utils.sessions.session_manager import session_manager

router = Router()


@router.callback_query(F.data == 'stats')
async def statistic(call: types.CallbackQuery, bot: Bot):
    text = "📊 Статистика сессий\n\n"

    message = await call.message.answer('🕔 Загрузка статистики..')
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            full_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
            avg_text = await get_average_response_time(client)

            text += (
                f"👱🏻‍♂️ {full_name}\n"
                f"— 🕔 Сред. время ответа: {avg_text}\n\n"
            )

        except Exception as e:
            text += f"❌ Ошибка сессии {user_id}: {str(e)}\n\n"
    text += '\n<blockquote>⚠️ Статистика считает от 10:00 до 20:00</blockquote>'

    await bot.edit_message_text(text, message_id=message.message_id, chat_id=call.message.chat.id)

    await call.message.answer(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже', reply_markup=start_kb.as_markup())
