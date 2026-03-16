# Файл: src/layer04_swarm/engine.py

import json
import asyncio
from src.layer00_utils.config_manager import config
from src.layer03_brain.llm.client import client_openai, key_manager

# Импортируем НОВЫЕ глобальные переменные
from src.layer03_brain.agent.skills.registry import skills_registry, openai_tools, l0_manifest
from src.layer04_swarm.tools.system_tools import system_tools_registry, system_tools_l0_manifest

SYBAGENT_MODEL = config.swarm.sybagent_model
MAX_SYBAGENT_STEPS = config.swarm.max_sybagent_steps

async def _execute_tool(subagent, tool_call):
    """Изолированная функция для выполнения навыка через единый роутер (execute_skill) для субагентов."""
    func_name = tool_call.function.name
    
    if func_name != "execute_skill":
        subagent.add_log(f"Перехвачена галлюцинация LLM: попытка прямого вызова {func_name}.")
        return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": "System Error: Прямой вызов запрещен. Необходимо использовать 'execute_skill'."}

    try:
        args = json.loads(tool_call.function.arguments)
    except Exception as e:
        return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": f"JSON Error: {e}"}

    skill_uri = args.pop("skill_uri", None)
    if not skill_uri:
        return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": "System Error: Отсутствует 'skill_uri'."}

    subagent.add_log(f"Вызов L2 инструмента: {skill_uri}")

    # 1. Системные инструменты субагента (им нужен объект subagent)
    if skill_uri in system_tools_registry:
        try:
            result = await system_tools_registry[skill_uri](subagent, **args)
            return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": str(result)}
        except Exception as e:
            subagent.add_log(f"Ошибка в {skill_uri}: {e}")
            return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": f"TypeError: {e}"}

    # 2. Обычные инструменты (из глобального реестра)
    # Субагент просит тулзу по её старому "name", но в реестре она лежит по "uri". 
    # В L0 манифесте субагента мы будем писать URI так: 'aaf://sandbox/read_sandbox_file'.
    if skill_uri in skills_registry:
        
        # Защита: проверяем, есть ли этот навык (его короткое имя) в allowed_tools субагента
        short_name = skill_uri.split("/")[-1]
        if short_name not in subagent.allowed_tools:
             return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": f"System Error: Навык '{skill_uri}' запрещен для твоей роли."}
             
        try:
            target_func = skills_registry[skill_uri]
            if asyncio.iscoroutinefunction(target_func):
                result = await target_func(**args)
            else:
                result = await asyncio.to_thread(target_func, **args)
            
            result_str = str(result)
            if len(result_str) > 80000:
                result_str = result_str[:80000] + "... [ОБРЕЗАНО]"
            return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": result_str}
            
        except TypeError as e:
            subagent.add_log(f"Ошибка типов в {skill_uri}: {e}")
            return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": f"TypeError (Неверные параметры): {e}"}
        except Exception as e:
            subagent.add_log(f"Критическая ошибка в {skill_uri}: {e}")
            return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": f"Error: {e}"}

    return {"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": f"System Error: Навык '{skill_uri}' не найден."}

def _build_subagent_l0_manifest(allowed_tools: list) -> str:
    """Динамически собирает L0 справочник только из РАЗРЕШЕННЫХ субагенту инструментов"""
    lines = [
        "## L0 SKILL LIBRARY (Доступные инструменты)",
        "ЕДИНСТВЕННЫЙ способ взаимодействия с системой — вызов инструмента `execute_skill(skill_uri, **kwargs)`.\n"
    ]
    
    # 1. Добавляем системные тулзы (Делегирование, Эскалация, Тревога)
    lines.append("[SYSTEM (Swarm)]")
    for sig in system_tools_l0_manifest:
        lines.append(sig)
    lines.append("")
    
    # 2. Добавляем разрешенные глобальные тулзы
    for category, skills in l0_manifest.items():
        category_skills = []
        for skill in skills:
            # Ищем, разрешен ли этот скилл (по короткому имени)
            for allowed in allowed_tools:
                # В сигнатуре навык записан как `aaf://category/allowed_name(...)`
                if f"/{allowed}(" in skill:
                    category_skills.append(skill)
                    break
        
        if category_skills:
            lines.append(f"[{category.upper()}]")
            for skill in category_skills:
                lines.append(skill)
            lines.append("")
            
    return "\n".join(lines).strip()

async def run_subagent_react(subagent, task_query: str) -> str:
    """ReAct цикл для субагентов"""
    
    # Собираем микро-манифест
    subagent_l0_manifest = _build_subagent_l0_manifest(subagent.allowed_tools)
    
    # Вшиваем манифест прямо в конец system_prompt субагента
    full_system_prompt = f"{subagent.system_prompt}\n\n{subagent_l0_manifest}"

    messages = [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": task_query}
    ]

    steps = 0
    while steps < MAX_SYBAGENT_STEPS:
        steps += 1
        client_openai.api_key = await key_manager.get_next_key()

        try:
            response = await client_openai.chat.completions.create(
                model=SYBAGENT_MODEL,
                messages=messages,
                tools=openai_tools, # ПЕРЕДАЕМ ТОЛЬКО ЕДИНУЮ СХЕМУ execute_skill
                tool_choice="auto"
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or "Пустой ответ от субагента."

            messages.append(msg)

            tasks = [_execute_tool(subagent, tc) for tc in msg.tool_calls]
            results = await asyncio.gather(*tasks)
            messages.extend(results)

            if getattr(subagent, 'is_delegated', False) or getattr(subagent, 'is_escalated', False):
                return "Цикл прерван системно (эстафета или эскалация)."

        except Exception as e:
            subagent.add_log(f"Критическая ошибка API: {e}")
            return f"Субагент упал с ошибкой API: {e}"

    return "Превышен лимит шагов ReAct. Субагент принудительно остановлен."