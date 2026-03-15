import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from openai import AsyncOpenAI

# Единый менеджер
from src.layer00_utils.env_manager import AGENT_NAME
from src.layer00_utils.logger import system_logger

API_URL = os.getenv("API_URL")

if API_URL and not API_URL.startswith(("http://", "https://")):
    if "localhost" in API_URL or "127.0.0.1" in API_URL:
        API_URL = f"http://{API_URL}"
    else:
        API_URL = f"https://{API_URL}"

# Ищем в переменных окружения профиля все ключи, которые начинаются на "LLM_API_KEY_"
ALL_KEYS = [value for key, value in os.environ.items() if key.startswith("LLM_API_KEY_") and value.strip()]

current_dir = Path(__file__).resolve()
src_dir = next((p for p in current_dir.parents if p.name == "src"), None)
project_root = src_dir.parent if src_dir else current_dir.parents[3]

# Динамический путь до state_file для каждого отдельного агента (Agents/{AGENT_NAME}/workspace/api_keys_state.json)
AGENT_WORKSPACE = project_root / "Agents" / AGENT_NAME / "workspace"
STATE_FILE = str(AGENT_WORKSPACE / "api_keys_state.json")

class KeyManager:
    def __init__(self, keys):
        self.all_keys = keys.copy()
        self.active_keys = keys.copy()
        self.exhausted_keys = []
        self.current_index = 0
        self.requests_today = 0 
        self._lock = None 
        
        # Инициализация времени (Московское время UTC+3)
        msk_tz = timezone(timedelta(hours=3))
        now_msk = datetime.now(msk_tz)
        
        if now_msk.hour >= 12:
            self.last_reset_date = now_msk.date()
        else:
            self.last_reset_date = now_msk.date() - timedelta(days=1)
            
        self._sync_load_state()

    @property
    def lock(self):
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def _mask_key(self, key: str) -> str:
        if not key or len(key) <= 10:
            return "***[INVALID_KEY]***"
        return f"{key[:10]}...[MASKED]"

    def _sync_load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    
                saved_date_str = state.get("last_reset_date")
                if saved_date_str:
                    saved_date = datetime.strptime(saved_date_str, "%Y-%m-%d").date()
                    if saved_date == self.last_reset_date:
                        saved_masked_keys = state.get("exhausted_keys", [])
                        
                        self.exhausted_keys = [
                            k for k in self.all_keys 
                            if self._mask_key(k) in saved_masked_keys
                        ]
                        
                        self.requests_today = state.get("requests_today", 0)
                        self.active_keys = [k for k in self.all_keys if k not in self.exhausted_keys]
                        system_logger.info(f"[APIKeyManager] Состояние восстановлено. Активных ключей: {len(self.active_keys)}")
            except Exception as e:
                system_logger.error(f"[APIKeyManager] Ошибка загрузки состояния: {e}")

    def _sync_save_state(self):
        try:
            # ДИНАМИЧЕСКИЙ ПУТЬ
            os.makedirs(AGENT_WORKSPACE, exist_ok=True)
            state = {
                "last_reset_date": self.last_reset_date.strftime("%Y-%m-%d"),
                "exhausted_keys": [self._mask_key(k) for k in self.exhausted_keys],
                "requests_today": self.requests_today
            }
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            system_logger.error(f"[APIKeyManager] Ошибка сохранения состояния: {e}")

    async def _check_daily_reset(self):
        msk_tz = timezone(timedelta(hours=3))
        now_msk = datetime.now(msk_tz)
        
        if now_msk.date() > self.last_reset_date and now_msk.hour >= 12:
            if self.exhausted_keys:
                system_logger.info(f"[APIKeyManager] 12:00 МСК. Сброс квот. Восстановлено ключей: {len(self.exhausted_keys)}")
                self.active_keys.extend(self.exhausted_keys)
                self.exhausted_keys.clear()
            self.requests_today = 0 
            self.last_reset_date = now_msk.date()
            await asyncio.to_thread(self._sync_save_state)

    async def get_next_key(self) -> str:
        async with self.lock:
            await self._check_daily_reset()
            
            if not self.active_keys:
                system_logger.critical("[APIKeyManager] Все ключи исчерпаны. Ждем 12:00 МСК.")
                return "ALL_KEYS_EXHAUSTED"
                
            key = self.active_keys[self.current_index % len(self.active_keys)]
            self.current_index += 1
            self.requests_today += 1
            
            if self.requests_today % 10 == 0:
                await asyncio.to_thread(self._sync_save_state)
                
            return key

    async def mark_key_exhausted(self, key: str):
        async with self.lock:
            if key in self.active_keys:
                self.active_keys.remove(key)
                self.exhausted_keys.append(key)
                
                system_logger.warning(f"[APIKeyManager] Ключ {self._mask_key(key)} улетел в лимит (429). Убран из пула. Осталось живых: {len(self.active_keys)}")
                
                if self.active_keys:
                    self.current_index = self.current_index % len(self.active_keys)
                    
                await asyncio.to_thread(self._sync_save_state)

    @property
    def total_active(self):
        return len(self.active_keys)

    def get_api_status_string(self) -> str:
        total = len(self.all_keys)
        active = len(self.active_keys)
        return f"Активных API-ключей: {active}/{total} | API запросов за сегодня: {self.requests_today}"

key_manager = KeyManager(ALL_KEYS)

client_openai = AsyncOpenAI(
    api_key="DUMMY_KEY",
    base_url=API_URL
)