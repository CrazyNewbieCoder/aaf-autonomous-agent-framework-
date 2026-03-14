from src.layer03_brain.agent.skills.auto_schema import llm_skill

@llm_skill(
    description="Создает специализированного субагента для выполнения фоновых/рутинных задач.",
    parameters={
        "role": {"description": "Класс субагента.", "enum": ["Researcher", "SystemAnalyst", "ChatSummarizer", "WebMonitor", "Chronicler"]},
        "name": "Уникальное имя субагента.",
        "instructions": "Подробная инструкция, что именно он должен сделать.",
        "trigger_condition": "ТОЛЬКО ДЛЯ ДЕМОНОВ. Условие для тревоги.",
        "interval_sec": "ТОЛЬКО ДЛЯ ДЕМОНОВ. Интервал сна между проверками в секундах."
    }
)
async def spawn_subagent(role: str, name: str, instructions: str, trigger_condition: str = None, interval_sec: int = None) -> str:
    from src.layer04_swarm.manager import swarm_manager
    return await swarm_manager.spawn_subagent(role, name, instructions, trigger_condition, interval_sec)

@llm_skill(
    description="Прерывает запущенный процесс субагента по его имени.", 
    parameters={
        "name": "Имя субагента."
    }
)
async def kill_subagent(name: str) -> str:
    from src.layer04_swarm.manager import swarm_manager
    return await swarm_manager.kill_subagent(name)

@llm_skill(
    description="Обновление параметров уже запущенного субагента без его остановки.",
    parameters={
        "name": "Имя активного субагента.",
        "instructions": "(Опционально) Новые инструкции.",
        "trigger_condition": "(Опционально) Новое условие для тревоги.",
        "interval_sec": "(Опционально) Новый интервал сна."
    }
)
async def update_subagent(name: str, instructions: str = None, trigger_condition: str = None, interval_sec: int = None) -> str:
    from src.layer04_swarm.manager import swarm_manager
    return await swarm_manager.update_subagent(name, instructions, trigger_condition, interval_sec)