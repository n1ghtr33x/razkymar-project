from pyrogram import Client, idle
from config import api_id, api_hash, test_mode

async def start_pyrogram(session_name, session_string):
    app = Client(
        session_name,
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_string,
        app_version='0.0.1',
        in_memory=True,
        test_mode=test_mode
    )

    @app.on_message()
    async def handle_message(client, message):
        print(f"[Pyrogram] Получено сообщение: {message.text}")

    await app.start()

    await idle()
    await app.stop()