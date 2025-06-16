from pyrogram import Client
from typing import Dict

from pyrogram.enums import ChatType
from pyrogram.types import Chat


def split_by_chunks(text, chunk_size=4096):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def plural(n: int, one: str, few: str, many: str) -> str:
    if 11 <= (n % 100) <= 14:
        return many
    elif n % 10 == 1:
        return one
    elif 2 <= (n % 10) <= 4:
        return few
    else:
        return many

def format_seconds_to_text(seconds: float) -> str:
    seconds = int(seconds)
    parts = []

    days = seconds // 86400
    if days > 0:
        parts.append(f"{days} {plural(days, 'день', 'дня', 'дней')}")
    seconds %= 86400

    hours = seconds // 3600
    if hours > 0:
        parts.append(f"{hours} {plural(hours, 'час', 'часа', 'часов')}")
    seconds %= 3600

    minutes = seconds // 60
    if minutes > 0:
        parts.append(f"{minutes} {plural(minutes, 'минута', 'минуты', 'минут')}")
    seconds %= 60

    if seconds > 0 or not parts:
        parts.append(f"{seconds} {plural(seconds, 'секунда', 'секунды', 'секунд')}")

    return " ".join(parts)

async def get_average_response_time(client: Client, max_messages: int = 400, delta_limit: int = 84600) -> str:
    me = await client.get_me()
    user_id = me.id
    response_times = []
    per_chat_averages: Dict[str, float] = {}

    async for dialog in client.get_dialogs():
        chat: Chat = dialog.chat
        chat_name = chat.title or chat.first_name or str(chat.id)

        if chat.type != ChatType.PRIVATE:
            continue

        messages = []
        async for msg in client.get_chat_history(chat.id, limit=max_messages):
            messages.append(msg)

        messages.reverse()

        last_other_msg = None
        chat_response_times = []

        for msg in messages:
            if not msg.from_user or msg.from_user.is_bot:
                continue

            if msg.from_user.id != user_id:
                last_other_msg = msg
            elif last_other_msg and last_other_msg.date:
                delta = msg.date - last_other_msg.date
                delta_sec = delta.total_seconds()
                if 0 < delta_sec < delta_limit:
                    response_times.append(delta_sec)
                    chat_response_times.append(delta_sec)
                last_other_msg = None

        if chat_response_times:
            avg = sum(chat_response_times) / len(chat_response_times)
            per_chat_averages[chat_name] = avg

    if response_times:
        overall_avg_sec = sum(response_times) / len(response_times)
        average_text = format_seconds_to_text(overall_avg_sec)
    else:
        average_text = "0 секунд"

    return average_text

