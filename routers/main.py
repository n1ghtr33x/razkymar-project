from aiogram import Router, types
from aiogram.filters import Command
from utils.keyboards import start_kb

router = Router()


@router.message(Command('start'))
async def add_client(message: types.Message):
    await message.answer(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже', reply_markup=start_kb.as_markup())
