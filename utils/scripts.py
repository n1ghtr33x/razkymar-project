import logging
from io import BytesIO

from pyrogram import Client
from typing import Dict, Any, Optional

from pyrogram.enums import ChatType, ParseMode

from datetime import time, timezone, timedelta, datetime


def split_by_chunks(text, chunk_size=4096):
    """
    принимает текст и возвращает список по элементам текст длина которого chunk_size
    :param text: текст
    :param chunk_size: длина текста
    :return:
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def plural(n: int, one: str, few: str, many: str) -> str:
    """
    функция для возврата в какой множине должен быть текст
    :param n:
    :param one:
    :param few:
    :param many:
    :return:
    """
    if 11 <= (n % 100) <= 14:
        return many
    elif n % 10 == 1:
        return one
    elif 2 <= (n % 10) <= 4:
        return few
    else:
        return many


def format_seconds_to_text(seconds: float) -> str:
    """
    форматирование текста для времени
    :param seconds:
    :return:
    """
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

    gmt_plus_2 = timezone(timedelta(hours=2))

    start_time = time(10, 0)  # 10:00
    end_time = time(22, 0)  # 22:00

    async for dialog in client.get_dialogs():
        chat = dialog.chat
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

            msg_time = msg.date.astimezone(gmt_plus_2)
            msg_time_only = msg_time.time()

            if not (start_time <= msg_time_only <= end_time):
                continue

            if msg.from_user.id != user_id:
                last_other_msg = msg
            elif last_other_msg and last_other_msg.date:

                last_other_msg_time = last_other_msg.date.astimezone(gmt_plus_2).time()
                if not (start_time <= last_other_msg_time <= end_time):
                    last_other_msg = None
                    continue

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


async def broadcast_one(client: Client, text: str, months: int, photo: Optional[BytesIO] = None) -> list[Any]:
    successful = 0
    fail = 0

    gmt_plus_2 = timezone(timedelta(hours=2))

    async for dialog in client.get_dialogs():
        chat = dialog.chat

        if chat.type != ChatType.PRIVATE:
            continue

        messages = []
        async for msg in client.get_chat_history(chat.id, limit=100):
            messages.append(msg)

        diff_months = 0

        for msg in messages:
            if not msg.from_user or msg.from_user.is_bot:
                continue

            msg_time = msg.date.astimezone(gmt_plus_2)

            now = datetime.now(gmt_plus_2)

            msg_total_months = msg_time.year * 12 + msg_time.month
            now_total_months = now.year * 12 + now.month

            diff_months = now_total_months - msg_total_months

            break

        if months == 0:
            try:
                if photo:
                    await client.send_photo(
                        chat_id=chat.id,
                        photo=photo,
                        caption=text,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await client.send_message(
                        chat_id=chat.id,
                        text=text,
                        parse_mode=ParseMode.HTML
                    )
                successful += 1
            except Exception as e:
                fail += 1
                logging.info(f"❌ Ошибка при отправке в {chat.id}: {e}")
                pass
        elif diff_months >= months:
            try:
                if photo:
                    await client.send_photo(
                        chat_id=chat.id,
                        photo=photo,
                        caption=text,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await client.send_message(
                        chat_id=chat.id,
                        text=text,
                        parse_mode=ParseMode.HTML
                    )
                successful += 1
            except Exception as e:
                fail += 1
                logging.info(f"❌ Ошибка при отправке в {chat.id}: {e}")

    return [successful, fail]


async def broadcast_multiply(clients: list[Client], text: str, months: int, photo: Optional[BytesIO] = None) -> list[Any]:
    successful = 0
    fail = 0

    gmt_plus_2 = timezone(timedelta(hours=2))
    for client in clients:
        async for dialog in client.get_dialogs():
            chat = dialog.chat

            if chat.type != ChatType.PRIVATE:
                continue

            messages = []
            async for msg in client.get_chat_history(chat.id, limit=100):
                messages.append(msg)

            diff_months = 0

            for msg in messages:
                if not msg.from_user or msg.from_user.is_bot:
                    continue

                msg_time = msg.date.astimezone(gmt_plus_2)

                now = datetime.now(gmt_plus_2)

                msg_total_months = msg_time.year * 12 + msg_time.month
                now_total_months = now.year * 12 + now.month

                diff_months = now_total_months - msg_total_months

                break

            if months == 0:
                try:
                    if photo:
                        await client.send_photo(
                            chat_id=chat.id,
                            photo=photo,
                            caption=text,
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await client.send_message(
                            chat_id=chat.id,
                            text=text,
                            parse_mode=ParseMode.HTML
                        )
                    successful += 1
                except Exception as e:
                    fail += 1
                    logging.info(f"❌ Ошибка при отправке в {chat.id}: {e}")
            elif diff_months >= months:
                try:
                    if photo:
                        await client.send_photo(
                            chat_id=chat.id,
                            photo=photo,
                            caption=text,
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await client.send_message(
                            chat_id=chat.id,
                            text=text,
                            parse_mode=ParseMode.HTML
                        )
                    successful += 1
                except Exception as e:
                    fail += 1
                    logging.info(f"❌ Ошибка при отправке в {chat.id}: {e}")

    return [successful, fail]
