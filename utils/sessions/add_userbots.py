import asyncio
import logging

from pyrogram import Client, idle
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageIdInvalid
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
            me = await app.get_me()
            if message.from_user.id == me.id:
                if message.text == '!проверить':
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

                                    if dialog.chat.id == message.chat.id:
                                        if len(user_mess) >= 10:
                                            await message.edit_text(text='Пользователь существует')
                                            return
                            except Exception as e:
                                logging.warning(f"Ошибка при получении {user_id}: {e}")
                        value = {
                            'users': users
                        }
                        db.set('core.users', 'old_users', value)
                        us = db.get('core.users', 'old_users')
                        if us:
                            for i in us['users']:
                                if i == message.chat.id:
                                    await message.edit_text(text='Пользователь существует')
                                    return
                        await message.edit_text('Пользователя не существует')
                    except MessageIdInvalid as ex:
                        logging.info(f'warning: {ex}')
            else:
                status = db.get('core.autoresponder', 'status', False)
                if status:
                    users = db.get('core.autoresponder', 'users', [])
                    if me.id in users['users']:
                        data = db.get('core.autoresponder', 'data', {'text': 'wd', 'photo': None})
                        text = data['text']
                        photo = data['photo']
                        if photo is not None:
                            await app.send_photo(chat_id=message.chat.id, photo=photo, caption=text)
                        else:
                            await app.send_message(chat_id=message.chat.id, text=text, parse_mode=ParseMode.MARKDOWN)

        try:
            await app.start()
            await idle()
        except UpdatesTooLong:
            print("[Pyrogram] UpdatesTooLong — перезапуск клиента через 5 секунд...")
            await app.stop()
            await asyncio.sleep(5)
            continue
        except Exception as e:
            print(f"[Pyrogram] Ошибка: {e}")
            await app.stop()
            break
        else:
            await app.stop()
            break
