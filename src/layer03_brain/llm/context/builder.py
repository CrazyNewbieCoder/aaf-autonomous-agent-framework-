import asyncio


from src.layer00_utils.watchdog.watchdog import watchdog
from src.layer00_utils.workspace import workspace_manager

from src.layer01_datastate.memory_manager import memory_manager
from src.layer01_datastate.global_state.global_state_monitoring import global_state_monitoring
from src.layer01_datastate.sql_db.management.mental_state import get_all_mental_states
from src.layer01_datastate.sql_db.management.dialogue import get_clear_recent_dialogue
from src.layer01_datastate.sql_db.management.long_term_tasks import get_all_tasks
from src.layer01_datastate.sql_db.management.agent_actions import get_recent_agent_actions
from src.layer04_swarm.manager import swarm_manager

from src.layer03_brain.agent.skills.telegram.logic import get_unread_tg_summary



class ContextBuilder:
    def __init__(self):
        pass

    async def _fetch_base_context(self, limits):
        """Единый метод сбора базовых данных для ВСЕХ циклов"""
        tasks = {
            "global_state": global_state_monitoring.get_global_state(),
            "mental_state": get_all_mental_states(),

            "recent_thoughts": memory_manager.get_formatted_thoughts(limit=limits.thoughts_limit),
            "recent_actions": get_recent_agent_actions(limit=limits.actions_limit),
            "recent_dialogues": get_clear_recent_dialogue(limit=limits.dialogue_limit),

            "unread_tg": get_unread_tg_summary(),
            "system_health": watchdog.get_system_modules_report(),
            "tasks": get_all_tasks(),
            "swarm_status": swarm_manager.get_swarm_status(),
            "sandbox_files": asyncio.to_thread(workspace_manager.get_sandbox_files_list),
            "macro_arch": self._get_macro_architecture_map(), 
        }

        keys = list(tasks.keys())
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Автоматически оборачиваем всё в _safe_get и собираем обратно в словарь
        return {key: self._safe_get(res) for key, res in zip(keys, results)}