import kuzu
import asyncio
from pathlib import Path
from src.layer00_utils.env_manager import AGENT_NAME
from src.layer00_utils.logger import system_logger
from src.layer00_utils.config_manager import config
from src.layer00_utils.watchdog.watchdog import graph_db_module
from src.layer01_datastate.event_bus.event_bus import event_bus
from src.layer01_datastate.event_bus.events import Events

current_dir = Path(__file__).resolve()
src_dir = next((p for p in current_dir.parents if p.name == "src"), None)
project_root = src_dir.parent if src_dir else current_dir.parents[3]

# Динамический путь для каждого отдельного агента
# KuzuDB будет лежать в Agents/{AGENT_NAME}/workspace/_data/kuzu_db/
GRAPH_DB_PATH = str(project_root / "Agents" / AGENT_NAME / config.memory.kuzu_db_path)

db = None
conn = None

def _init_kuzu_sync():
    """Синхронная инициализация KuzuDB и создание схемы (если её нет)"""
    global db, conn
    
    Path(GRAPH_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    db = kuzu.Database(GRAPH_DB_PATH)
    conn = kuzu.Connection(db)
    
    try:
        conn.execute("MATCH (n:Concept) RETURN n LIMIT 1")
    except RuntimeError:
        system_logger.info(f"[Graph DB] Создание схемы графа для '{AGENT_NAME}' (Nodes: Concept, Edges: Link)...")

        conn.execute("CREATE NODE TABLE Concept(name STRING, type STRING, PRIMARY KEY (name))")
        conn.execute("CREATE REL TABLE Link(FROM Concept TO Concept, base_type STRING, context STRING, updated_at STRING, confidence_score DOUBLE, bond_weight DOUBLE)")

async def setup_graph_db():
    """Асинхронная обертка для старта базы"""
    try:
        await asyncio.to_thread(_init_kuzu_sync)
        system_logger.info(f"[Graph DB] Графовая база данных успешно подключена (Директория: {GRAPH_DB_PATH}).")
        await event_bus.publish(Events.SYSTEM_MODULE_HEARTBEAT, module_name=graph_db_module, status="ON")
        
        event_bus.subscribe(Events.STOP_SYSTEM, stop_graph_db)
    except Exception as e:
        system_logger.error(f"[Graph DB] Ошибка инициализации KuzuDB: {e}")
        await event_bus.publish(Events.SYSTEM_MODULE_ERROR, module_name=graph_db_module, status="ERROR", error_msg=str(e))

async def stop_graph_db(*args, **kwargs):
    """Корректное закрытие графовой БД"""
    global db, conn
    if conn:
        conn.close()
    if db:
        db.close()
    system_logger.info(f"[Graph DB] База данных агента '{AGENT_NAME}' сохранена и остановлена.")