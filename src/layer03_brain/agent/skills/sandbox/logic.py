from src.layer00_utils.workspace import workspace_manager
from src.layer00_utils.sandbox_env.executor import execute_once
from src.layer00_utils.sandbox_env.deployments import deploy_project, manage_deployments
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

@llm_skill(
    description="Деплоит полноценный микросервис (Docker-контейнер) из папки проекта в Sandbox. Контейнер будет работать 24/7.",
    parameters={
        "vfs_path": "VFS путь к папке проекта (например: 'sandbox/projects/my_api').",
        "project_name": "Уникальное имя для проекта (только латиница, цифры и '_').",
        "env_vars": "(Опционально) Словарь переменных окружения. Например: {'TOKEN': '123'}.",
        "entrypoint": "(Опционально) Главный файл запуска (по умолчанию 'main.py')."
    }
)
async def deploy_sandbox_project(vfs_path: str, project_name: str, env_vars: dict = None, entrypoint: str = "main.py") -> str:
    return await deploy_project(vfs_path, project_name, env_vars, entrypoint)

@llm_skill(
    description="Управление жизненным циклом запущенных микросервисов (чтение логов, перезапуск, удаление и т.д.).",
    parameters={
        "project_name": "Имя проекта, которое было указано при деплое.",
        "action": {"description": "Действие с контейнером.", "enum": ["logs", "stop", "restart", "destroy", "stats"]},
        "lines": "(Опционально) Количество строк лога для чтения (по умолчанию 100, только для action='logs')."
    }
)
async def manage_sandbox_deployments(project_name: str, action: str, lines: int = 100) -> str:
    return await manage_deployments(project_name, action, lines)