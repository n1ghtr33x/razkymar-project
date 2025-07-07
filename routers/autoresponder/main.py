import os
from io import BytesIO

from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import BufferedInputFile
from aiogram.utils.text_decorations import markdown_decoration, html_decoration

from utils.keyboards import on_off_kb, start_kb, autoresponder_kb, autoresponder_users

from utils.db import db

router = Router()


class AutoresponderStates(StatesGroup):
    on_off = State()
    autoresponder_preview = State()
    waiting_text = State()
    waiting_photo = State()
    select_users_state = State()


@router.callback_query(F.data == 'autoresponder')
async def autoresponder(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    status = db.get('core.autoresponder', 'status', False)
    status_text = '🚫 Выключено'
    if status:
        status_text = '✅ Включено'

    await call.message.answer(f'✅ Авто-Ответчик — Функция по авто-ответу всем чатам, в включённом состоянии'
                              f'\n'
                              f'\n ⚡️ Статус: {status_text}'
                              , reply_markup=on_off_kb())
    await state.set_state(AutoresponderStates.on_off)


@router.callback_query(F.data.in_(['autoresponder_on', 'autoresponder_off']), AutoresponderStates.on_off)
async def on_off(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    await call.message.delete()
    if data[1] == 'on':
        await state.set_state(AutoresponderStates.autoresponder_preview)
        await call.message.answer('ТУТ НУЖНО ИЗМЕНИТЬ ТЕКСТ', reply_markup=autoresponder_kb())
        return

    db.set('core.autoresponder', 'status', False)
    await call.message.answer('🚫 Авто-Ответчик был успешно выключён!')

    await call.message.answer(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже', reply_markup=start_kb.as_markup())

    await state.clear()


@router.callback_query(F.data == 'autoresponder_back', AutoresponderStates.autoresponder_preview)
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()

    await call.message.answer(f'🔥 Добро пожаловать в «Юзер Контроль Бота»\n\nВыберите одну из кнопок ниже', reply_markup=start_kb.as_markup())

    await state.clear()


# === Добавление текста ===
@router.callback_query(F.data == 'autoresponder_add_text', AutoresponderStates.autoresponder_preview)
async def add_text(call: types.CallbackQuery, state: FSMContext):
    if call.message.photo:
        await call.message.edit_caption(call.inline_message_id, '📄 Отправьте текст для сообщения', reply_markup=None)
    else:
        await call.message.edit_text('📄 Отправьте текст для сообщения', reply_markup=None)
    await state.set_state(AutoresponderStates.waiting_text)


@router.message(AutoresponderStates.waiting_text)
async def check_text(message: types.Message, state: FSMContext):
    await message.delete()

    formatted_text = html_decoration.unparse(message.text, message.entities)

    # Сохраняем текст
    await state.update_data(message_text=formatted_text)

    data = await state.get_data()
    photo = data.get("photo")

    if photo:
        await message.answer_photo(photo=photo, caption=formatted_text,
                                   reply_markup=autoresponder_kb())
    else:
        await message.answer(formatted_text, reply_markup=autoresponder_kb())

    await state.set_state(AutoresponderStates.autoresponder_preview)


# === Добавление фото ===
@router.callback_query(F.data == 'autoresponder_add_photo', AutoresponderStates.autoresponder_preview)
async def add_photo(call: types.CallbackQuery, state: FSMContext):
    if call.message.text:
        await call.message.edit_text("🖼 Отправьте фото для сообщения", reply_markup=None)
    else:
        await call.message.answer("🖼 Отправьте фото для сообщения")

    await state.set_state(AutoresponderStates.waiting_photo)


@router.message(AutoresponderStates.waiting_photo, F.photo)
async def check_photo(message: types.Message, state: FSMContext, bot: Bot):
    await message.delete()

    # Скачиваем и сохраняем фото
    file = await bot.get_file(message.photo[-1].file_id)
    byte_stream = BytesIO()
    await bot.download_file(file.file_path, destination=byte_stream)
    byte_stream.seek(0)
    photo = BufferedInputFile(byte_stream.read(), filename="photo.jpg")

    # Путь к сохранённому файлу
    file_path = f"photos/photo.jpg"

    # Создаём директорию, если нет
    os.makedirs("photos", exist_ok=True)

    # Скачиваем фото на диск
    await bot.download_file(file.file_path, destination=file_path)

    await state.update_data(photo=photo, photo_byte=file_path)

    # Достаём текст (если уже есть)
    data = await state.get_data()
    message_text = data.get("message_text", "")

    await message.answer_photo(photo=photo, caption=message_text,
                               reply_markup=autoresponder_kb())

    await state.set_state(AutoresponderStates.autoresponder_preview)


@router.callback_query(F.data == 'autoresponder_run', AutoresponderStates.autoresponder_preview)
async def go(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('🦾 Выберите аккаунты. На них будет включен авто-ответчик', reply_markup=await autoresponder_users(state))
    await state.set_state(AutoresponderStates.select_users_state)


@router.callback_query(F.data.startswith('autoresponder-user'), AutoresponderStates.select_users_state)
async def select_user(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    key = f"btn_{call.data.split('_')[2]}"

    current = data.get(key, False)
    new_value = not current

    if new_value == current:
        return

    await state.update_data({key: new_value})

    new_markup = await autoresponder_users(state)

    if call.message.reply_markup == new_markup:
        return

    await call.message.edit_reply_markup(reply_markup=new_markup)
    await call.answer("Обновлено ✅" if new_value else "Отключено ❌")


@router.callback_query(F.data == 'autoresponder_run')
async def run(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_text = data.get('message_text')
    photo = data.get('photo_byte', None)

    selected_ids = [int(k.split('_')[1]) for k, v in data.items() if k.startswith('btn_') and v is True]

    db.set('core.autoresponder', 'status', True)

    value = {
        'users': selected_ids
    }

    db.set('core.autoresponder', 'users', value)

    value = {
        'text': message_text,
        'photo': photo
    }

    db.set('core.autoresponder', 'data', value)

    await call.message.delete()
    await call.message.answer('✅ Авто-Ответчик был успешно включён!')
    await state.clear()
