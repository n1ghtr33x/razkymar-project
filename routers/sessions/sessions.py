import asyncio
from pathlib import Path

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import User

from config import api_id, api_hash, test_mode
from utils.keyboards import get_sessions_kb, start_kb, get_sessions_numbers
from utils.sessions.add_userbots import start_pyrogram
from utils.sessions.session_manager import session_manager

router = Router()

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(exist_ok=True)


class AuthStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()
    waiting_for_code2 = State()


@router.callback_query(F.data == 'sessions')
async def sessions(call: types.CallbackQuery):
    active_sessions = len(session_manager.active_sessions)
    await call.message.edit_text(f'🔗 <b>Подключенные Сессии</b>\n\n👱🏻‍♂️ {active_sessions} аккаунтов:')
    await call.message.edit_reply_markup(call.inline_message_id, await get_sessions_kb())


@router.callback_query(F.data == 'back')
async def back(call: types.CallbackQuery):
    await call.message.edit_text(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже',
                                 reply_markup=start_kb.as_markup())


@router.callback_query(F.data.startswith("add_session"))
async def new_session(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📱 Введите номер телефона. Пример: +48 111 222 333 или +48111222333:")
    await state.set_state(AuthStates.waiting_for_phone)


async def create_client(session_path: Path) -> Client:
    client = Client(
        name=session_path.as_posix(),
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
        test_mode=test_mode
    )

    return client


@router.message(AuthStates.waiting_for_phone, F.text.regexp(r'^\+\d[\d ]{10,20}$'))
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text
    session_path = SESSION_DIR / f"session_{phone}"

    try:
        client = Client(
            name=session_path.as_posix(),
            api_id=api_id,
            api_hash=api_hash,
            in_memory=True,
            test_mode=test_mode
        )

        await client.connect()
        sent_code = await client.send_code(phone)

        await state.update_data(
            phone=phone,
            phone_code_hash=sent_code.phone_code_hash,
            client=client
        )

        await message.answer("💬 Введите код №1. Отправьте код, Который пришёл на аккаунт который вы хотите добавить:")
        await state.set_state(AuthStates.waiting_for_code)

    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        await state.clear()


@router.message(AuthStates.waiting_for_code, F.text.regexp(r'^\d+$'))
async def process_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client = data["client"]
    code = message.text

    try:
        await client.sign_in(
            phone_number=data["phone"],
            phone_code=code,
            phone_code_hash=data["phone_code_hash"]
        )

        if await session_manager.save_session(data["phone"], client):
            try:
                session_path = SESSION_DIR / f"session2_{data['phone']}"
                client = await create_client(session_path)
                await client.connect()
                sent_code = await client.send_code(data['phone'])
                await state.update_data(phone_code_hash2=sent_code.phone_code_hash,
                                        client2=client)
                await message.answer(
                    "💬 Введите код №2. Отправьте код, Который пришёл на аккаунт который вы хотите добавить:")

                await state.set_state(AuthStates.waiting_for_code2)
            except Exception as e:
                await message.answer(f"Ошибка: {str(e)}")
                await state.clear()
        else:
            await message.answer("❌ Не удалось сохранить сессию")
            await state.clear()

    except SessionPasswordNeeded:
        await message.answer("🔐 Введите пароль 2FA:")
        await state.set_state(AuthStates.waiting_for_password)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@router.message(AuthStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client = data["client"]
    password = message.text

    try:
        await client.check_password(password)

        if await session_manager.save_session(data["phone"], client):
            try:
                session_path = SESSION_DIR / f"session2_{data['phone']}"
                client = await create_client(session_path)
                await client.connect()
                sent_code = await client.send_code(data['phone'])
                await state.update_data(phone_code_hash2=sent_code.phone_code_hash,
                                        client2=client, password=password)
                await message.answer(
                    "💬 Введите код №2. Отправьте код, Который пришёл на аккаунт который вы хотите добавить:")

                await state.set_state(AuthStates.waiting_for_code2)
            except Exception as e:
                await message.answer(f"Ошибка: {str(e)}")
                await state.clear()
        else:
            await message.answer("❌ Не удалось сохранить сессию")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


@router.message(AuthStates.waiting_for_code2)
async def process_code2(message: types.Message, state: FSMContext):
    data = await state.get_data()
    client = data["client2"]
    code = message.text
    password = data.get('password', None)

    try:
        await client.sign_in(
            phone_number=data["phone"].replace(' ', ''),
            phone_code=code,
            phone_code_hash=data["phone_code_hash2"]
        )

        if await session_manager.save_second_session(data["phone"], client):
            me = await client.get_me()
            asyncio.create_task(start_pyrogram(f'ses_{me.phone_number}', await client.export_session_string()))
            await message.answer(
                f"✅ УСПЕШНО ДОБАВЛЕНА СЕССИЯ\n"
                f"🏷 Имя: {me.first_name}\n"
                f"📱 Номер телефона: +{me.phone_number}"
            )
            await message.answer(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже', reply_markup=start_kb.as_markup())
        else:
            await message.answer("❌ Не удалось сохранить сессию")
            await state.clear()
    except SessionPasswordNeeded:
        try:
            await client.check_password(password)
            if await session_manager.save_second_session(data["phone"], client):
                me = await client.get_me()
                asyncio.create_task(start_pyrogram(f'ses_{me.phone_number}', await client.export_session_string()))
                await message.answer(
                    f"✅ УСПЕШНО ДОБАВЛЕНА СЕССИЯ\n"
                    f"🏷 Имя: {me.first_name}\n"
                    f"📱 Номер телефона: +{me.phone_number.replace(' ', '')}"
                )
                await message.answer(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже', reply_markup=start_kb.as_markup())
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()
    finally:
        await state.clear()


@router.callback_query(F.data == 'remove_session')
async def remove_session(call: types.CallbackQuery):
    await call.message.edit_text('Выбери аккаунт для удаления:', reply_markup=await get_sessions_numbers())


@router.callback_query(F.data.startswith("phone_"))
async def numbers(call: types.CallbackQuery):
    number = call.data.split('_')[1]
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            if me.phone_number == number:
                await session_manager.delete_session(f'+{number}')
                await call.message.answer('Сессия успешно удалена!')
                active_sessions = len(session_manager.active_sessions)
                await call.message.answer(f'🔗 <b>Подключенные Сессии</b>\n\n👱🏻‍♂️ {active_sessions} аккаунтов:',
                                          reply_markup=await get_sessions_kb())
                return
        except Exception as e:
            await call.message.answer(f"❌ Ошибка сессии: {str(e)}\n\n")
