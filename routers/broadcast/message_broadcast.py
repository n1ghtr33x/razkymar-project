import logging

from aiogram import Router, types, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import BufferedInputFile
from pyrogram.types import User

from utils.keyboards import broadcast_mk, start_kb, broadcast_kb, active_users_kb, broadcast_time_kb, \
    active_users_multiple, main_menu_broadcast
from utils.scripts import broadcast_one, broadcast_multiply
from utils.sessions.session_manager import session_manager
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.markdown import html_decoration
from io import BytesIO

router = Router()

users = []
text = ''


class StatesState(StatesGroup):
    waiting_text = State()
    waiting_photo = State()
    broadcasting_preview = State()
    broadcast_time_state = State()

    select_users_state = State()


@router.callback_query(F.data == 'broadcast')
async def broadcast(call: types.CallbackQuery):
    await call.message.edit_text('🦾 <b>Сколько аккаунтов хотите использовать?</b> Выберите категорию количества '
                                 'аккаунтов', reply_markup=broadcast_mk.as_markup())


@router.callback_query(F.data == 'broadcast_back')
async def back(call: types.CallbackQuery, state: FSMContext):
    if call.message.photo:
        await call.message.delete()
        await call.message.answer(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже', reply_markup=start_kb.as_markup())
        await state.clear()
    else:
        await call.message.edit_text(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже', reply_markup=start_kb.as_markup())
        await state.clear()


@router.callback_query(F.data == 'broadcast_multiple')
async def broadcast_multiple(call: types.CallbackQuery, state: FSMContext):
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            users.append(me.id)
        except Exception as e:
            logging.warning(f"Ошибка при получении {user_id}: {e}")

    if not users:
        await call.message.edit_text("❌ Не удалось загрузить ни одного клиента.")
        await state.clear()
        return

    await call.message.edit_text('🤖 <b>Выберите аккаунт.</b> Выбранные аккаунты будут участвовать в рассылке', reply_markup=await active_users_multiple(state))
    await state.set_state(StatesState.select_users_state)


@router.callback_query(F.data.startswith('broadcast-user-multiple'), StatesState.select_users_state)
async def select_user(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    key = f"btn_{call.data.split('_')[2]}"

    current = data.get(key, False)
    new_value = not current

    if new_value == current:
        return

    await state.update_data({key: new_value})

    new_markup = await active_users_multiple(state)

    if call.message.reply_markup == new_markup:
        return

    await call.message.edit_reply_markup(reply_markup=new_markup)
    await call.answer("Обновлено ✅" if new_value else "Отключено ❌")


@router.callback_query(F.data == 'broadcast_go')
async def start_editing(call: types.CallbackQuery, state: FSMContext):
    clients = []

    data = await state.get_data()

    # Получаем ID выбранных пользователей
    selected_ids = [int(k.split('_')[1]) for k, v in data.items() if k.startswith('btn_') and v is True]

    if not selected_ids:
        await call.answer("❌ Никто не выбран")
        return

    # Собираем подходящие клиенты
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            if me.id in selected_ids:
                users.append(me.id)
                clients.append(client)
        except Exception as e:
            logging.warning(f"Ошибка при получении {user_id}: {e}")

    # Ничего не найдено
    if not users:
        await call.message.edit_text("❌ Не удалось загрузить ни одного клиента.")
        await state.clear()
        return

    # Сохраняем в FSM: список клиентов и user_ids
    await state.update_data(broadcast_clients=clients, broadcast_user_ids=users, multiply=True)

    # Переход к следующему состоянию
    await state.set_state(StatesState.broadcasting_preview)

    # Отправляем ОДНО сообщение
    await call.message.edit_text(
        f"☘️ Рассылка будет отправлена на {len(users)} аккаунт(ов).",
        reply_markup=broadcast_kb()
    )


@router.callback_query(F.data == 'broadcast_one')
async def broadcast_1(call: types.CallbackQuery):
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            users.append(me.id)
        except Exception as e:
            logging.warning(f"Ошибка при получении {user_id}: {e}")

    if not users:
        await call.message.edit_text("❌ Не удалось загрузить ни одного клиента.")
        return
    await call.message.edit_text(f'🤖 <b>Выберите аккаунт.</b> Выбранные аккаунты будут участвовать в рассылке', reply_markup=await active_users_kb())


@router.callback_query(F.data.startswith("broadcast_user_"))
async def select_user(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split('_')

    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            if me.id == int(data[2]):
                await call.message.edit_text(f'☘️Рассылка для: {me.first_name}', reply_markup=broadcast_kb())
                users.append(me.id)
                await state.update_data(client=client)
                await state.set_state(StatesState.broadcasting_preview)
        except Exception as e:
            await call.message.edit_text(f"❌ Ошибка: {str(e)}\n\n")
            await state.clear()


# === Добавление текста ===
@router.callback_query(F.data == 'broadcast_add_text', StatesState.broadcasting_preview)
async def add_text(call: types.CallbackQuery, state: FSMContext):
    if call.message.photo:
        await call.message.edit_caption(call.inline_message_id, '📄 Отправьте текст для рассылки', reply_markup=None)
    else:
        await call.message.edit_text('📄 Отправьте текст для рассылки', reply_markup=None)
    await state.set_state(StatesState.waiting_text)


@router.message(StatesState.waiting_text)
async def check_text(message: types.Message, state: FSMContext):
    await message.delete()

    # Форматируем текст
    formatted_text = html_decoration.unparse(message.text, message.entities)

    await state.update_data(message_text=formatted_text)

    data = await state.get_data()
    photo = data.get("photo")

    if photo:
        await message.answer_photo(photo=photo, caption=formatted_text,
                                   reply_markup=broadcast_kb())
    else:
        await message.answer(formatted_text, reply_markup=broadcast_kb())

    await state.set_state(StatesState.broadcasting_preview)


# === Добавление фото ===
@router.callback_query(F.data == 'broadcast_add_photo', StatesState.broadcasting_preview)
async def add_photo(call: types.CallbackQuery, state: FSMContext):
    if call.message.text:
        await call.message.edit_text("🖼 Отправьте фото для рассылки", reply_markup=None)
    else:
        await call.message.answer("🖼 Отправьте фото для рассылки")

    await state.set_state(StatesState.waiting_photo)


@router.message(StatesState.waiting_photo, F.photo)
async def check_photo(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()

    # Скачиваем и сохраняем фото
    file = await bot.get_file(message.photo[-1].file_id)
    byte_stream = BytesIO()
    await bot.download_file(file.file_path, destination=byte_stream)
    byte_stream.seek(0)
    photo = BufferedInputFile(byte_stream.read(), filename="photo.jpg")
    await state.update_data(photo=photo)

    # Достаём текст (если уже есть)
    data = await state.get_data()
    message_text = data.get("message_text", "")

    await message.answer_photo(photo=photo, caption=message_text,
                               reply_markup=broadcast_kb())

    await state.set_state(StatesState.broadcasting_preview)


@router.callback_query(F.data == 'broadcast_time')
async def broadcast_time(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer('⏳ Выберите время', reply_markup=broadcast_time_kb())
    await state.set_state(StatesState.broadcast_time_state)


@router.callback_query(lambda c: c.data and c.data.startswith('broadcast_time_'),
                       StateFilter(StatesState.broadcast_time_state))
async def select_time(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split('_')[2]

    if data == 'one':
        await state.update_data(broad_time='0')
    elif data == '1':
        await state.update_data(broad_time='1')
    elif data == '3':
        await state.update_data(broad_time='3')
    elif data == '6':
        await state.update_data(broad_time='6')

    await state.set_state(StatesState.broadcasting_preview)
    await call.message.delete()


@router.callback_query(F.data == 'broadcast_run', StatesState.broadcasting_preview)
async def send(call: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    if data.get('multiply', False):
        message_text = data.get('message_text')
        clients = data.get('broadcast_clients')
        broad_time = int(data.get('broad_time', 0))
        photo = None
        await call.message.delete()
        await call.message.answer('Рассылка запущена!')
        if call.message.photo:
            file = await bot.get_file(call.message.photo[-1].file_id)
            byte_stream = BytesIO()
            await bot.download_file(file.file_path, destination=byte_stream)
            byte_stream.seek(0)
            byte_stream.name = 'image.jpg'
            photo = byte_stream
        try:
            broad = await broadcast_multiply(clients, message_text, broad_time, photo)
            await call.message.answer(f'Рассылка завершена!\n\nУспешно: {broad[0]}\nНеудачно: {broad[1]}')
        except Exception as e:
            await call.message.answer(f"❌ Ошибка: {str(e)}\n\n")
        await state.clear()
    else:
        message_text = data.get('message_text')
        client = data.get('client')
        broad_time = int(data.get('broad_time', 0))
        photo = None
        await call.message.delete()
        await call.message.answer('⌛️ Рассылка началась. Ожидайте результатов. Вы так же можете закончить рассылку досрочно')
        if call.message.photo:
            file = await bot.get_file(call.message.photo[-1].file_id)
            byte_stream = BytesIO()
            await bot.download_file(file.file_path, destination=byte_stream)
            byte_stream.seek(0)
            byte_stream.name = 'image.jpg'
            photo = byte_stream
        try:
            broad = await broadcast_one(client, message_text, broad_time, photo)
            await call.message.answer(f'<b>🏁 РАССЫЛКА ЗАКОНЧЕНА!</b>\n<u>💭 Чаты:</u>\n<blockquote>✅ Успешно: <b>{broad[0]} чатов</b>\n🚫 Не удачно: <b>{broad[1]} чатов</b></blockquote>', reply_markup=main_menu_broadcast.as_markup())
        except Exception as e:
            await call.message.answer(f"❌ Ошибка: {str(e)}\n\n")
        await state.clear()


@router.callback_query(F.data == 'broadcast_all')
async def broadcast_all(call: types.CallbackQuery, state: FSMContext):
    clients = []
    for user_id, client in session_manager.active_sessions.items():
        try:
            me: User = await client.get_me()
            users.append(me.id)
            clients.append(client)
        except Exception as e:
            logging.warning(f"Ошибка при получении {user_id}: {e}")

    if not users:
        await call.message.edit_text("❌ Не удалось загрузить ни одного клиента.")
        await state.clear()
        return

    await state.update_data(broadcast_clients=clients, broadcast_user_ids=users, multiply=True)

    await state.set_state(StatesState.broadcasting_preview)

    await call.message.edit_text(
        f"☘️ Рассылка будет отправлена на {len(users)} аккаунт(ов).",
        reply_markup=broadcast_kb()
    )
