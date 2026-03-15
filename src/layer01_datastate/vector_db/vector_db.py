from pathlib import Path
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import os
import warnings

# 1. Единый менеджер и конфиги
from src.layer00_utils.env_manager import AGENT_NAME
from src.layer00_utils.config_manager import config
from src.layer00_utils.logger import system_logger
from src.layer00_utils.watchdog.watchdog import vector_db_module
from src.layer01_datastate.event_bus.event_bus import event_bus
from src.layer01_datastate.event_bus.events import Events

warnings.filterwarnings("ignore", category=UserWarning, message=".*Could not reconstruct embedding function.*")

current_dir = Path(__file__).resolve()
src_dir = next((p for p in current_dir.parents if p.name == "src"), None)
project_root = src_dir.parent if src_dir else current_dir.parents[3]

# Динамические пути для каждого отдельного агента
# ChromaDB будет лежать в Agents/{AGENT_NAME}/workspace/_data/chroma_db/
CHROMA_DB_DIRECTORY = str(project_root / "Agents" / AGENT_NAME / config.memory.chroma_db_path)
# Путь к локальной модели BAAI остается ОБЩИМ для всех агентов, чтобы не качать гигабайты дублей
LOCAL_EMBEDDING_MODEL_PATH = str(project_root / config.memory.embedding_model.local_path)

embedding_model = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=LOCAL_EMBEDDING_MODEL_PATH,
    device="cpu"
)

client = chromadb.PersistentClient(path=CHROMA_DB_DIRECTORY) 

COLLECTIONS = {
    "agent_vector_db": client.get_or_create_collection(
        name="agent_vector_db", 
        embedding_function=embedding_model
    ),
    "agent_thoughts_vector_db": client.get_or_create_collection(
        name="agent_thoughts_vector_db", 
        embedding_function=embedding_model
    ),
    "user_vector_db": client.get_or_create_collection(
        name="user_vector_db", 
        embedding_function=embedding_model
    )
}

def _get_col(collection_name: str):
    if collection_name not in COLLECTIONS:
        raise ValueError(f"[Vector DB] Коллекция '{collection_name}' не найдена.")
    return COLLECTIONS[collection_name]

async def stop_vector_db(*args, **kwargs):
    system_logger.info(f"[Vector DB] База данных агента '{AGENT_NAME}' сохранена и остановлена.")

async def setup_vector_db():
    system_logger.info(f"[Vector DB] База данных инициализирована (Директория: {CHROMA_DB_DIRECTORY}).")
    event_bus.subscribe(Events.STOP_SYSTEM, stop_vector_db)
    await event_bus.publish(Events.SYSTEM_MODULE_HEARTBEAT, module_name=vector_db_module, status="ON")