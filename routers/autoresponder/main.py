from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()


@router.callback_query(F.data == 'autoresponder')
async def autoresponder(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(call.data)
