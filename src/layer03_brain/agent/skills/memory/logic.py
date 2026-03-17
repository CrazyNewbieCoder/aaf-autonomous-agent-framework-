from src.layer01_datastate.memory_manager import memory_manager
from src.layer01_datastate.graph_db.graph_db_management import manage_graph as m_g, explore_graph as e_g, get_full_graph as g_f_g, delete_from_graph as d_f_g
from src.layer03_brain.agent.skills.auto_schema import llm_skill

@llm_skill(description="Асинхронный поиск по всем векторным базам данных. Возвращает отсортированный по релевантности список фактов, знаний и твоих прошлых мыслей.", parameters={"queries": "Список поисковых запросов."})
async def recall_memory(queries: list) -> str:
    return await memory_manager.recall_memory(queries)

@llm_skill(
    description="Сохраняет информацию в VectorDB.", 
    parameters={
        "topic": {"description": "Категория информации.", "enum": ["user_fact", "system_knowledge", "introspection"]}, 
        "text": "Текст для запоминания."
    }
)
async def memorize_information(topic: str, text: str) -> str:
    return await memory_manager.memorize_information(topic, text)

@llm_skill(
    description="Удаляет записи из VectorDB по ID.", 
    parameters={
        "collection_name": {"description": "Имя коллекции", "enum": ["user_vector_db", "agent_vector_db", "agent_thoughts_vector_db"]}, 
        "ids": "Список ID записей для удаления."
    }
)
async def forget_information(collection_name: str, ids: list) -> str:
    return await memory_manager.forget_information(collection_name, ids)

@llm_skill(
    description="Единое управление Mental State.",
    parameters={
        "action": {"description": "'upsert' - создать/обновить. 'delete' - удалить.", "enum": ["upsert", "delete"]},
        "name": "Имя сущности.",
        "category": {"description": "Категория.", "enum": ["subject", "place", "artifact", "system"]},
        "tier": {"description": "Уровень важности.", "enum": ["critical", "high", "medium", "low"]},
        "description": "Фундаментальное описание.", "status": "Текущий статус.", "context": "Дополнительные заметки.", "rules": "Правила взаимодействия."
    }
)
async def manage_entity(action: str, name: str, category: str = None, tier: str = None, description: str = None, status: str = None, context: str = None, rules: str = None) -> str:
    return await memory_manager.manage_entity(action, name, category, tier, description, status, context, rules)

@llm_skill(
    description="Диспетчер долгосрочных задач.",
    parameters={
        "action": {"description": "Действие с задачей.", "enum": ["get_all", "create", "update", "delete"]},
        "task_id": "ID задачи.", "description": "Описание задачи.",
        "status": {"description": "Статус задачи.", "enum": ["pending", "in_progress", "paused", "completed", "failed"]},
        "term": "Срок или периодичность.", "context": "Рабочие заметки/прогресс по задаче."
    }
)
async def manage_task(action: str, task_id: int = None, description: str = None, status: str = None, term: str = None, context: str = None) -> str:
    return await memory_manager.manage_task(action, task_id, description, status, term, context)

@llm_skill(
    description="Позволяет искать в старых логах действий/диалогах.", 
    parameters={
        "target": {"description": "Где искать", "enum": ["dialogue", "actions"]}, 
        "query": "Текст для поиска.", "action_type": "Фильтр по навыку.", 
        "source": "Фильтр по источнику.", "days_ago": "За последние N дней.", 
        "limit": "Максимум результатов."
    }
)
async def deep_history_search(target: str, query: str = None, action_type: str = None, source: str = None, days_ago: int = None, limit: int = 50) -> str:
    return await memory_manager.deep_history_search(target, query, action_type, source, days_ago, limit)

@llm_skill(
    description="Возвращает единую хронологию последних событий.", 
    parameters={
        "limit": "Количество записей (по умолчанию 50)."
    }
)
async def get_chronicle_timeline(limit: int = 50) -> str:
    return await memory_manager.get_chronicle_timeline(limit)

@llm_skill(
    description="Возвращает все записи из указанной векторной коллекции.", 
    parameters={
        "collection_name": {"description": "Имя коллекции", "enum": ["user_vector_db", "agent_vector_db", "agent_thoughts_vector_db"]}
    }
)
async def get_all_vector_memory(collection_name: str) -> str:
    return await memory_manager.get_all_vector_memory(collection_name)

@llm_skill(
    description="Создает или обновляет связь между двумя узлами в графовой нейронной сети.",
    parameters={
        "source": "Имя исходного узла.", 
        "target": "Имя целевого узла.",
        "base_type": {"description": "Строгий базовый тип связи.", "enum":["RELATES_TO", "OPPOSED_TO", "CREATOR_OF", "MEMBER_OF", "DEPENDS_ON", "PART_OF", "RESOLVES", "CAUSED", "FOLLOWS", "REFERENCES", "USES_TOOL"]},
        "context": "Свободный текст. Твои мысли, причины или нюансы этой связи.",
        "confidence_score": {
            "description": "Уверенность в достоверности информации. 1.0 - абсолютный факт, 0.2 - неподтвержденный слух.", 
            "type": "number", 
            "enum":[0.2, 0.4, 0.6, 0.8, 1.0]
        },
        "bond_weight": {
            "description": "Сила/важность связи. 1.0 - критически важно для системы/пользователя, 0.2 - незначительная деталь.", 
            "type": "number", 
            "enum":[0.2, 0.4, 0.6, 0.8, 1.0]
        }
    }
)
async def manage_graph(source: str, target: str, base_type: str, context: str = "[Нет контекста]", confidence_score: float = 0.6, bond_weight: float = 0.6) -> str:
    return await m_g(source, target, base_type, context, confidence_score, bond_weight)

@llm_skill(
    description="Исследует графовую базу данных. Находит узел по имени и возвращает все его связи.", 
    parameters={
        "query": "Имя узла для поиска."
    }
)
async def explore_graph(query: str) -> str:
    return await e_g(query)

@llm_skill(
    description="Возвращает всё содержимое графовой базы данных."
)
async def get_full_graph() -> str:
    return await g_f_g()

@llm_skill(
    description="Удаляет данные из графовой базы. Если передать только source_node - узел будет стерт полностью.", 
    parameters={
        "source_node": "Имя узла.", "target_node": "(Опционально) Имя второго узла для удаления связи."
    }
)
async def delete_from_graph(source_node: str, target_node: str = None) -> str:
    return await d_f_g(source_node, target_node)

@llm_skill(
    description="Мета-программирование личности. Взаимодействия с правилами поведения.",
    parameters={
        "action": {"description": "Действие", "enum": ["add", "remove", "get_all"]}, 
        "trait": "Сама формулировка правила.", 
        "reason": "Логическое обоснование.", 
        "trait_id": "ID черты для удаления."
    }
)
async def manage_personality(action: str, trait: str = None, trait_id: int = None, reason: str = None) -> str:
    return await memory_manager.manage_personality(action, trait, trait_id, reason)