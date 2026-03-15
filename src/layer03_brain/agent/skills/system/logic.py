import asyncio 
from collections import deque
import os
from pathlib import Path
from src.layer00_utils.config_manager import config
from src.layer00_utils.logger import system_logger
from src.layer03_brain.agent.skills.auto_schema import llm_skill

@llm_skill(
    description="Изменяет интервал твоего проактивного цикла.",
    parameters={"seconds": "Новый интервал в секундах"}
)
def change_proactivity_interval(seconds: int) -> str:
    from src.layer03_brain.agent.engine.engine import brain_engine
    try:
        if seconds < brain_engine.min_cooldown:
            return f"Ошибка: Интервал не может быть меньше минимального кулдауна ({brain_engine.min_cooldown} сек) во избежание перерасхода бюджета."
        
        old_interval = brain_engine.proactivity_interval
        brain_engine.proactivity_interval = seconds
        brain_engine.target_proactive_time = brain_engine.last_proactive_time + seconds
        
        system_logger.info(f"[Proactivity ReAct] Интервал проактивности успешно изменен с {old_interval} сек. на {seconds} сек.")
        return f"[Proactivity ReAct] Интервал проактивности успешно изменен с {old_interval} сек. на {seconds} сек."
    except Exception as e:
        return f"Ошибка при изменении интервала: {e}"
    

@llm_skill(
    description="Изменяет интервал твоего цикла интроспекции.",
    parameters={"seconds": "Новый интервал в секундах"}
)
def change_thoughts_interval(seconds: int) -> str:
    from src.layer03_brain.agent.engine.engine import brain_engine
    try:
        if seconds < 10:
            return "Ошибка: Интервал не может быть меньше 10 секунд (во избежание перегрузки БД)."
        
        old_interval = brain_engine.thoughts_interval
        brain_engine.thoughts_interval = seconds
        
        system_logger.info(f"[Thoughts ReAct] Интервал интроспекции успешно изменен с {old_interval} сек. на {seconds} сек.")
        return f"[Thoughts ReAct] Интервал интроспекции успешно изменен с {old_interval} сек. на {seconds} сек."
    except Exception as e:
        return f"[Thoughts ReAct] Ошибка при изменении интервала интроспекции: {e}"


@llm_skill(
    description="Читает последние записи из твоего системного лога системы (system.log). Полезно для дебаггинга.",
    parameters={"lines": "Количество последних строк для чтения (по умолчанию 50)."}
)
async def read_recent_logs(lines: int = 50) -> str:
    from src.layer00_utils.env_manager import AGENT_NAME # <--- Добавляем импорт здесь

    current_dir = Path(__file__).resolve()
    src_dir = next((p for p in current_dir.parents if p.name == "src"), None)
    
    if not src_dir:
        return "Ошибка: Не удалось найти директорию src."
        
    # Теперь путь ведет в папку конкретного агента: Agents/NAME/logs/system.log
    project_root = src_dir.parent
    log_path = project_root / "Agents" / AGENT_NAME / "logs" / "system.log"
    
    def _read_tail():
        if not os.path.exists(log_path):
            return f"Файл логов не найден по пути: {log_path}"
        with open(log_path, 'r', encoding='utf-8') as f:
            tail = deque(f, maxlen=lines)
        if not tail:
            return "Файл логов пуст."
        return "".join(tail)
        
    try:
        result = await asyncio.to_thread(_read_tail)
        return f"Последние {lines} строк из логов агента {AGENT_NAME}:\n\n{result}"
    except Exception as e:
        return f"Ошибка при чтении логов: {e}"
    

@llm_skill(description="Инициирует корректное завершение работы всего твоего системного ядра (Docker-контейнера).")
async def shutdown_system() -> str:
    import os
    import signal
    from src.layer01_datastate.event_bus.event_bus import event_bus
    from src.layer01_datastate.event_bus.events import Events
    
    system_logger.warning("[System] Агент инициировал завершение работы системы.")
    await event_bus.publish(Events.STOP_SYSTEM)
    await asyncio.sleep(5)
    os.kill(os.getpid(), signal.SIGTERM)
    return "Сигнал на завершение работы отправлен. Базы сохранены, система отключается..."


@llm_skill(
    description="Изменяет твое вычислительное ядро (LLM-модель).",
    parameters={
        "new_model": {
            "description": "Точное название новой модели.", 
            "enum": config.llm.available_models
        }
    }
)
async def change_llm_model(new_model: str) -> str:
    if new_model not in config.llm.available_models:
        return f"Ошибка: Модель '{new_model}' не поддерживается. Доступные: {', '.join(config.llm.available_models)}"
    try:
        config.llm.model_name = new_model
        import src.layer03_brain.agent.engine.react as react_module
        react_module.LLM_MODEL = new_model
        
        current_dir = Path(__file__).resolve()
        yaml_path = current_dir.parents[4] / "config" / "settings.yaml"
        
        if not yaml_path.exists():
            return f"Модель изменена в памяти на '{new_model}', но файл settings.yaml не найден для сохранения."
            
        def _update_yaml():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            with open(yaml_path, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip().startswith("model_name:"):
                        indent = line[:len(line) - len(line.lstrip())]
                        f.write(f'{indent}model_name: "{new_model}"\n')
                    else:
                        f.write(line)
                        
        await asyncio.to_thread(_update_yaml)
        system_logger.warning(f"[System] LLM-модель успешно изменена на: {new_model}")
        return f"Системная архитектура обновлена. Новая модель '{new_model}' активирована и сохранена в конфигурации."
    except Exception as e:
        return f"Ошибка при смене модели: {e}"