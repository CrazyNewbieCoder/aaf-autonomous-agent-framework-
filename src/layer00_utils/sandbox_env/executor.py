# Файл: src/layer00_utils/sandbox_env/executor.py

import asyncio
from src.layer00_utils.logger import system_logger
from src.layer00_utils.workspace import workspace_manager
from src.layer00_utils.env_manager import AGENT_NAME # Единый менеджер

MAX_OUTPUT_LENGTH = 80000 

def _truncate_output(text: str) -> str:
    if not text:
        return ""
    if len(text) > MAX_OUTPUT_LENGTH:
        half = MAX_OUTPUT_LENGTH // 2
        return text[:half] + "\n\n... [ВЫВОД ОБРЕЗАН ИЗ-ЗА ЛИМИТОВ КОНТЕКСТА] ...\n\n" + text[-half:]
    return text

async def execute_once(filename: str, timeout: int = 120) -> str:
    try:
        filepath = workspace_manager.get_sandbox_file(filename)
        
        if not filepath.exists():
            return f"[Error] Файл '{filename}' не найден в директории sandbox."

        system_logger.info(f"[Sandbox] Запуск '{filename}' в Docker DinD (Агент: {AGENT_NAME}, Таймаут: {timeout}с).")

        # Динамический путь для Docker Wolumes для каждого отдельного агента
        # /app/Agents/{AGENT_NAME}/workspace/sandbox
        sandbox_path = f"/app/Agents/{AGENT_NAME}/workspace/sandbox"

        docker_cmd = [
            "docker", "run",
            "--rm",                                         
            "--memory=1g",                                  
            "--cpus=1",                                     
            "--pids-limit=100", 
            "--network=host",
            # Передаем имя агента внутрь эфемерного контейнера для agent_sdk.py
            "-e", f"MASTER_AGENT=agent_{AGENT_NAME.lower()}",
            # Пробрасываем ТОЛЬКО папку текущего агента
            "-v", f"{sandbox_path}:{sandbox_path}",         
            "-w", sandbox_path,
            "python:3.11-slim",                             
            "python", filename                              
        ]

        process = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except OSError:
                pass
            system_logger.warning(f"[Sandbox] Скрипт '{filename}' превысил таймаут {timeout}с и был убит.")
            return f"[Timeout Error] Скрипт выполнялся дольше {timeout} секунд."

        out_str = stdout.decode('utf-8', errors='replace').strip()
        err_str = stderr.decode('utf-8', errors='replace').strip()

        out_str = _truncate_output(out_str)
        err_str = _truncate_output(err_str)

        result = f"--- STDOUT ---\n{out_str if out_str else 'Пусто'}"
        if err_str:
            result += f"\n\n--- STDERR ---\n{err_str}"

        system_logger.debug(f"[Sandbox] Выполнение '{filename}' завершено (Код выхода: {process.returncode}).")
        return result

    except Exception as e:
        system_logger.error(f"[Sandbox] Ошибка выполнения '{filename}': {e}")
        return f"[System Error] Внутренняя ошибка песочницы: {e}"