import asyncio
from pathlib import Path

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded

from config import api_id, api_hash, test_mode
from utils.keyboards import start_kb
from utils.sessions.session_manager import session_manager
from utils.sessions.add_userbots import start_pyrogram

router = Router()

SESSION_DIR = Path("sessions")
SESSION_DIR.mkdir(exist_ok=True)


class AuthStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()
    waiting_for_code2 = State()


@router.message(Command('start'))
async def add_client(message: types.Message):
    if not session_manager.active_sessions:
        await message.answer(
            f"🔑 Привет {message.from_user.full_name}\n"
            "Используйте /add для добавления новой сессии"
        )
        return

    await message.answer(f'Добро пожаловать {message.from_user.full_name}.', reply_markup=start_kb.as_markup())


@router.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    await message.answer("Введите номер телефона (например, +48668412234):")
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


@router.message(AuthStates.waiting_for_phone, F.text.regexp(r'^\+[0-9]{11,15}$'))
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

        await message.answer("Код отправлен. Введите код из SMS:")
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
                await message.answer("Код 2 отправлен. Введите код из SMS:")

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
                await message.answer("Код 2 отправлен. Введите код из SMS:")

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
            phone_number=data["phone"],
            phone_code=code,
            phone_code_hash=data["phone_code_hash2"]
        )

        if await session_manager.save_second_session(data["phone"], client):
            me = await client.get_me()
            await message.answer(
                f"✅ Авторизация успешна!\n"
                f"👤 Имя: {me.first_name}\n"
                f"📱 Телефон: +{me.phone_number}"
            )

            await message.answer("✅ Сессия успешно загружена")
            asyncio.create_task(start_pyrogram(f'ses_{me.phone_number}', await client.export_session_string()))
        else:
            await message.answer("❌ Не удалось сохранить сессию")
            await state.clear()
    except SessionPasswordNeeded:
        try:
            await client.check_password(password)
            if await session_manager.save_second_session(data["phone"], client):
                me = await client.get_me()
                await message.answer(
                    f"✅ 2FA пройдена!\n"
                    f"👤 Имя: {me.first_name}\n"
                    f"📱 Телефон: +{me.phone_number}"
                )
                await message.answer("✅ Сессия успешно загружена")
                asyncio.create_task(start_pyrogram(f'ses_{me.phone_number}', await client.export_session_string()))
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()
    finally:
        await state.clear()
