import os
from pathlib import Path
from dotenv import load_dotenv


# 1. Получаем имя агента из системы (по умолчанию 'default_agent' для обратной совместимости)
AGENT_NAME = os.getenv("AGENT_NAME", "default_agent")

def load_agent_env():
    """Единая точка загрузки .env файла для конкретного агента"""
    current_dir = Path(__file__).resolve()
    src_dir = next((p for p in current_dir.parents if p.name == "src"), None)
    project_root = src_dir.parent if src_dir else current_dir.parents[2]

    # Путь: AAF/Agents/{AGENT_NAME}/.env
    env_path = project_root / "Agents" / AGENT_NAME / ".env"

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        # Не критично при билде докера, но предупредим
        print(f"[ENV Manager] Внимание: Файл .env не найден по пути {env_path}")

# Вызываем при импорте модуля
load_agent_env()