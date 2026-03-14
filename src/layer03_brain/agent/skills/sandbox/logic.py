import asyncio 
import os
from src.layer00_utils.workspace import workspace_manager
from src.layer00_utils.sandbox_env.executor import execute_once
from src.layer00_utils.sandbox_env.manager import _start_background_python_script, _kill_background_python_script, _get_running_python_scripts
from src.layer03_brain.agent.skills.auto_schema import llm_skill

@llm_skill(
    description="Разово запускает Python-скрипт из папки sandbox в изолированном Docker-контейнере.", 
    parameters={
        "filename": "Имя файла в песочнице."
    }
)
async def _execute_python_script(filename: str) -> str:
    return await execute_once(filename)

@llm_skill(
    description="Запускает Python-скрипт из папки sandbox как бесконечного фонового демона.", 
    parameters={
        "filename": "Имя файла в песочнице."
    }
)
async def start_background_python_script(filename: str) -> str:
    return await asyncio.to_thread(_start_background_python_script, filename)

@llm_skill(
    description="Принудительно завершает работу фонового Python-скрипта в песочнице.", 
    parameters={
        "filename": "Имя запущенного файла."
    }
)
async def kill_background_python_script(filename: str) -> str:
    return await asyncio.to_thread(_kill_background_python_script, filename)

@llm_skill(
    description="Возвращает список всех Python-скриптов, которые сейчас работают в фоне в песочнице."
)
async def get_running_python_scripts() -> str:
    running = await asyncio.to_thread(_get_running_python_scripts)
    if not running:
        return "В песочнице нет запущенных фоновых скриптов."
    lines = ["Запущенные фоновые скрипты:"]
    for fname, pid in running.items():
        lines.append(f"- {fname} (PID: {pid})")
    return "\n".join(lines)

@llm_skill(
    description="Удаляет указанный файл из твоей песочницы (workspace/sandbox/).", 
    parameters={
        "filename": "Имя файла для удаления."
    }
)
async def delete_sandbox_file(filename: str) -> str:
    try:
        clean_filename = os.path.basename(filename.replace("file:///", "").replace("/app/", ""))
        filepath = workspace_manager.get_sandbox_file(clean_filename)
        if not filepath.exists() or not filepath.is_file():
            return f"Ошибка: Файл '{clean_filename}' не найден в песочнице."
        await asyncio.to_thread(filepath.unlink)
        return f"Файл '{clean_filename}' успешно удален из песочницы."
    except Exception as e:
        return f"Ошибка при удалении файла: {e}"