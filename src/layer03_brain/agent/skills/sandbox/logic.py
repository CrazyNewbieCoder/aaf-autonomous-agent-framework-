from src.layer00_utils.workspace import workspace_manager
from src.layer00_utils.sandbox_env.executor import execute_once
from src.layer03_brain.agent.skills.auto_schema import llm_skill

@llm_skill(
    description="Разово выполняет Python-скрипт. Поднимает изолированный микро-контейнер, выдает результат и мгновенно умирает.",
    parameters={"filepath": "VFS путь к скрипту в песочнице (например: 'sandbox/scripts/parser.py')"}
)
async def execute_script(filepath: str) -> str:
    return await execute_once(filepath)

@llm_skill(
    description="Полностью очищает папку временных файлов."
)
def clean_temp_workspace() -> str:
    return workspace_manager.clean_temp_workspace()