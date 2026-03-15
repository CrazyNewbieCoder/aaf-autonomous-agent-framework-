import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Загружаем единый менеджер окружения (он уже подгрузил нужный .env агента)
from src.layer00_utils.env_manager import AGENT_NAME
from src.layer00_utils.logger import system_logger
from src.layer00_utils.watchdog.watchdog import sql_db_module
from src.layer01_datastate.event_bus.event_bus import event_bus
from src.layer01_datastate.event_bus.events import Events

# Настройки подключения (Берем из ENV агента)
SQL_DB_URL = os.getenv("SQL_DB_URL")

if not SQL_DB_URL:
    error_msg = f"Переменная SQL_DB_URL не найдена в .env профиля '{AGENT_NAME}'!"
    system_logger.critical(f"[SQL DB] {error_msg}")
    raise ValueError(error_msg)

# Имя схемы = имя агента в нижнем регистре (Postgres не любит заглавные буквы)
SCHEMA_NAME = AGENT_NAME.lower()

# Создаем асинхронный движок
# search_path=SCHEMA_NAME означает: "Всегда ищи и создавай таблицы в этой схеме по умолчанию"
engine = create_async_engine(
    SQL_DB_URL, 
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    connect_args={"server_settings": {"search_path": SCHEMA_NAME}}
)

async_session_factory = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Базовый класс для всех моделей
class Base(DeclarativeBase):
    # Явно указываем SQLAlchemy, в какой схеме живут наши таблицы
    __table_args__ = {"schema": SCHEMA_NAME}

async def stop_sql_db(*args, **kwargs):
    system_logger.info(f"[SQL DB] Отключение базы данных агента '{AGENT_NAME}'...")
    await engine.dispose()
    system_logger.info("[SQL DB] База данных успешно отключена.")

async def setup_sql_db():
    await event_bus.publish(Events.SYSTEM_MODULE_HEARTBEAT, module_name=sql_db_module, status="ON")
    event_bus.subscribe(Events.STOP_SYSTEM, stop_sql_db) 
    
    try:
        # Сначала создаем саму схему, если её нет (это нельзя сделать через Base.metadata)
        async with engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
            # После этого создаем все таблицы внутри схемы
            await asyncio.wait_for(conn.run_sync(Base.metadata.create_all), timeout=15.0)
            
        system_logger.info(f"[SQL DB] База данных успешно подключена (Схема: '{SCHEMA_NAME}').")
    except asyncio.TimeoutError:
        system_logger.error("[SQL DB] Ошибка: База данных не отвечает (Таймаут). Проверьте Docker.")
        raise
    except Exception as e:
        system_logger.error(f"[SQL DB] Ошибка подключения/инициализации схем: {e}")
        raise