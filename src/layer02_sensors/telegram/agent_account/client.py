import os
from telethon import TelegramClient
from pathlib import Path

# Единый менеджер и конфиги
from src.layer00_utils.env_manager import AGENT_NAME
from src.layer00_utils.config_manager import config
from src.layer00_utils.logger import system_logger

# Ключи читаются уже из загруженного профиля (env_manager отработал при импорте)
raw_api_id = os.getenv("TG_API_ID_AGENT")
TG_API_HASH_AGENT = os.getenv("TG_API_HASH_AGENT", "")

# Безопасный парсинг ID, чтобы не ронять весь проект при импорте
try:
    TG_API_ID_AGENT = int(raw_api_id) if raw_api_id else 0
except ValueError:
    system_logger.critical(f"[Telegram Telethon] Ошибка в профиле '{AGENT_NAME}': TG_API_ID_AGENT должен состоять только из цифр!")
    TG_API_ID_AGENT = 0

current_dir = Path(__file__).resolve()
src_dir = next((p for p in current_dir.parents if p.name == "src"), None)
project_root = src_dir.parent if src_dir else current_dir.parents[4]

# Динамический путь к сессии каждого отдельного агента (Agents/{AGENT_NAME}/workspace/_data/telegram_sessions)
SESSION_DIR = project_root / "Agents" / AGENT_NAME / "workspace" / "_data" / "telegram_sessions"
SESSION_DIR.mkdir(parents=True, exist_ok=True)

TG_AGENT_SESSION_NAME = config.telegram.agent_session_name

# Формируем полный путь к файлу сессии
session_path = os.path.join(SESSION_DIR, TG_AGENT_SESSION_NAME)

# Создаем клиента. ВАЖНО: Если ключей нет, Telethon все равно создаст объект,
# но при await agent_client.connect() в tg_manager.py он выдаст ошибку и WatchDog её поймает.
agent_client = TelegramClient(session_path, TG_API_ID_AGENT, TG_API_HASH_AGENT)