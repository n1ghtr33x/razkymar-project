import asyncio

from pyrogram import Client, idle
from pyrogram.raw.types import UpdatesTooLong

from config import api_id, api_hash, test_mode

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