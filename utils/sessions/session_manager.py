import asyncio
import json
import logging
from pathlib import Path
from typing import Dict
from pyrogram import Client
from pyrogram.enums import ParseMode

from config import test_mode
from utils.sessions.add_userbots import start_pyrogram


def delete_key_recursively(obj, key_to_delete):
    if isinstance(obj, dict):
        return {
            k: delete_key_recursively(v, key_to_delete)
            for k, v in obj.items()
            if k != key_to_delete
        }
    elif isinstance(obj, list):
        return [delete_key_recursively(item, key_to_delete) for item in obj]
    else:
        return obj


class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, Client] = {}
        self.active_second_sessions: Dict[str, Client] = {}
        self.sessions_file = Path("sessions/sessions.json")
        self.sessions_file.parent.mkdir(exist_ok=True)
        self.sessions_second_file = Path("sessions/second_sessions.json")
        self.sessions_second_file.parent.mkdir(exist_ok=True)

    async def delete_session(self, phone: str) -> bool:
        """Удаляет сессию из файла и закрывает клиента"""
        try:
            phone_key = phone.replace(' ', '')

            # Удаляем из файла
            if self.sessions_file.exists():
                with open(self.sessions_file, "r") as f:
                    sessions_data = json.load(f)

                with open(self.sessions_second_file, 'r') as f:
                    second_session_data = json.load(f)

                if phone_key in sessions_data:
                    del sessions_data[phone_key]
                    del second_session_data[phone_key]

                    with open(self.sessions_file, "w") as f:
                        json.dump(sessions_data, f, indent=4)

                    with open(self.sessions_second_file, 'w') as f:
                        json.dump(second_session_data, f, indent=4)

                    logging.info(f"🗑️ Сессия удалена из файла для {phone}")
                else:
                    logging.info(f"⚠️ Сессия для {phone} не найдена в файле")

            client = self.active_sessions.pop(phone_key, None)
            if client:
                await client.stop()
                logging.info(f"🔌 Клиент остановлен для {phone}")
            else:
                logging.info(f"⚠️ Клиент не найден в active_sessions для {phone}")

            return True
        except Exception as e:
            logging.info(f"❌ Ошибка удаления сессии {phone}: {str(e)}")
            return False

    async def load_sessions(self):
        """Загружаем все сессии из файла при старте"""
        if not self.sessions_file.exists():
            return

        with open(self.sessions_file, "r") as f:
            sessions_data = json.load(f)

        for phone, session_data in sessions_data.items():
            try:
                client = Client(
                    name=f"session_{phone}",
                    api_id=session_data["api_id"],
                    api_hash=session_data["api_hash"],
                    session_string=session_data["session_string"],
                    in_memory=True,
                    test_mode=test_mode,
                    parse_mode=ParseMode.MARKDOWN
                )
                await client.start()
                self.active_sessions[phone] = client
                logging.info(f"✅ Сессия восстановлена для {phone}")
            except Exception as e:
                logging.info(f"❌ Ошибка загрузки сессии {phone}: {str(e)}")

    async def load_second_sessions(self):
        """Загружаем все сессии из файла при старте"""
        if not self.sessions_second_file.exists():
            return

        with open(self.sessions_second_file, "r") as f:
            sessions_data = json.load(f)

        for phone, session_data in sessions_data.items():
            try:
                asyncio.create_task(start_pyrogram(f'{phone}', session_data["session_string"]))
            except Exception as e:
                logging.info(f"❌ Ошибка загрузки сессии {phone}: {str(e)}")

    async def save_session(self, phone: str, client: Client) -> bool:
        """Сохраняем сессию в файл"""
        try:
            session_string = await client.export_session_string()

            sessions_data = {}
            if self.sessions_file.exists():
                with open(self.sessions_file, "r") as f:
                    sessions_data = json.load(f)

            sessions_data[phone.replace(' ', '')] = {
                "api_id": client.api_id,
                "api_hash": client.api_hash,
                "session_string": session_string
            }

            with open(self.sessions_file, "w") as f:
                json.dump(sessions_data, f, indent=4)

            self.active_sessions[phone] = client
            logging.info(f"💾 Сессия сохранена для {phone}")
            return True
        except Exception as e:
            logging.info(f"❌ Ошибка сохранения сессии {phone}: {str(e)}")
            return False

    async def save_second_session(self, phone: str, client: Client) -> bool:
        """Сохраняем сессию в файл"""
        try:
            session_string = await client.export_session_string()
            sessions_data = {}
            if self.sessions_second_file.exists():
                with open(self.sessions_second_file, "r") as f:
                    sessions_data = json.load(f)

            sessions_data[phone.replace(' ', '')] = {
                "api_id": client.api_id,
                "api_hash": client.api_hash,
                "session_string": session_string
            }

            with open(self.sessions_second_file, "w") as f:
                json.dump(sessions_data, f, indent=4)

            self.active_second_sessions[phone] = client
            logging.info(f"💾 Сессия сохранена для {phone}")
            return True
        except Exception as e:
            logging.info(f"❌ Ошибка сохранения сессии {phone}: {str(e)}")
            return False

    async def stop_all_sessions(self):
        """Останавливаем все сессии"""
        for phone, client in list(self.active_sessions.items()):
            try:
                await client.disconnect()
            except:
                pass
            self.active_sessions.pop(phone, None)

        for phone, client in list(self.active_second_sessions.items()):
            try:
                await client.disconnect()
            except:
                pass
            self.active_second_sessions.pop(phone, None)


session_manager = SessionManager()
