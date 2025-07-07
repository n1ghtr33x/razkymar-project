import asyncio
import logging

from pyrogram import Client, idle
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageIdInvalid, FloodWait
from pyrogram.raw.types import UpdatesTooLong
from pyrogram.types import Message

from config import api_id, api_hash, test_mode
from utils.db import db


async def start_pyrogram(session_name, session_string):
    while True:
        app = Client(
            session_name,
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_string,
            app_version='0.0.1',
            in_memory=False,
            test_mode=test_mode
        )

        @app.on_message()
        async def autoresponder(_, message: Message):
            try:
                me = await app.get_me()
                if message.from_user.id == me.id:
                    if message.text.lower() == '!проверить':
                            us = db.get('core.users', 'old_users')
                            if us:
                                for i in us['users']:
                                    if i == message.chat.id:
                                        await message.edit_text(text='Пользователь существует')
                                        return
                            await message.edit_text('Пользователя не существует')

                    elif message.text.lower() == '!обновить список':
                        await message.edit_text('Обновление списка..')
                        users = []
                        try:
                            from .session_manager import session_manager
                            for user_id, client in session_manager.active_sessions.items():
                                try:
                                    async for dialog in client.get_dialogs():
                                        messages = []
                                        user_mess = []
                                        async for msg in client.get_chat_history(dialog.chat.id, limit=100):
                                            messages.append(msg)
                                        for msg in messages:
                                            if not msg.from_user or msg.from_user.is_bot:
                                                continue
                                            else:
                                                users.append(dialog.chat.id)
                                                user_mess.append(msg)
                                except Exception as e:
                                    logging.warning(f"Ошибка при получении {user_id}: {e}")
                            value = {
                                'users': users
                            }
                            db.set('core.users', 'old_users', value)

                            await message.edit_text('Список пользователей обновлен')
                        except MessageIdInvalid as ex:
                            logging.info(f'warning: {ex}')
                else:
                    print(message.text)
                    status = db.get('core.autoresponder', 'status', False)
                    if status:
                        users = db.get('core.autoresponder', 'users', [])
                        if me.id in users['users']:
                            data = db.get('core.autoresponder', 'data', {'text': 'None', 'photo': None})
                            text = data['text']
                            photo = data['photo']
                            if photo is not None:
                                await app.send_photo(chat_id=message.chat.id, photo=photo, caption=text,
                                                     parse_mode=ParseMode.HTML)
                            else:
                                await app.send_message(chat_id=message.chat.id, text=text, parse_mode=ParseMode.HTML)
                    users = db.get('core.users', 'old_users')
                    if users:
                        for i in users['users']:
                            if i == message.from_user.id:
                                return
                    await app.send_message(chat_id=message.chat.id, text='🎁 НОВЫЙ КЛИЕНТ! Вы получили скидку 10% от нашего магазина.')
                    if users:
                        users['users'] += message.chat.id
                    else:
                        users = {
                            'users': [message.chat.id]
                        }
                    db.set('core.users', 'old_users', users)
            except FloodWait:
                pass

        try:
            await app.start()
            await idle()
        except UpdatesTooLong:
            print("[Pyrogram] UpdatesTooLong — restarting client...")
            await app.stop()
            await asyncio.sleep(2)
            continue
        except Exception as e:
            print(f"[Pyrogram] except: {e}")
            await app.stop()
            break
        else:
            await app.stop()
            break
