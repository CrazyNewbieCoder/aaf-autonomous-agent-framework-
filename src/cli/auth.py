import os
import sys
import subprocess
from src.cli.colors import G, Y, R, C, W

def cmd_auth(agent_name: str):
    agent_name = agent_name.upper()
    agent_dir = os.path.join("Agents", agent_name)
    
    if not os.path.exists(agent_dir):
        print(f"{R}[X] Ошибка: Профиль агента '{agent_name}' не найден!{W}")
        return
        
    print(f"\n{C}=== Авторизация Telegram для агента '{agent_name}' ==={W}")
    
    env_path = os.path.join(agent_dir, ".env")
    api_id = ""
    api_hash = ""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TG_API_ID_AGENT="):
                    api_id = line.split("=", 1)[1].strip()
                elif line.startswith("TG_API_HASH_AGENT="):
                    api_hash = line.split("=", 1)[1].strip()
                    
    if not api_id or not api_hash:
        print(f"{R}[X] Ошибка: TG_API_ID_AGENT и/или TG_API_HASH_AGENT не заполнены.{W}")
        return
        
    try:
        api_id = int(api_id)
    except ValueError:
        print(f"{R}[X] Ошибка: TG_API_ID_AGENT должен состоять только из цифр.{W}")
        return

    try:
        from telethon import TelegramClient
    except ImportError:
        print(f"{Y}Установка Telethon для локальной авторизации.{W}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon"])
        from telethon import TelegramClient

    session_dir = os.path.join(agent_dir, "workspace/_data/telegram_sessions")
    os.makedirs(session_dir, exist_ok=True)
    session_path = os.path.join(session_dir, "agent_session")
    
    print(f"{G}Запуск клиента Telethon.{W}")
    client = TelegramClient(session_path, api_id, api_hash)
    client.start()
    print(f"\n{G}[V] Авторизация успешно завершена. Файл сессии сохранен.{W}")
    client.disconnect()