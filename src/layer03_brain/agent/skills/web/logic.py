import os
import asyncio
from tavily import TavilyClient
from src.layer00_utils.logger import system_logger
from src.layer00_utils.web_tools import _web_search, _read_webpage, _get_habr_articles, _get_habr_news
from src.layer03_brain.agent.skills.auto_schema import llm_skill

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

@llm_skill(
    description="Ищет информацию в интернете (Google/DuckDuckGo). Возвращает список релевантных ссылок.", 
    parameters={
        "query": "Поисковый запрос (например: 'новости ИИ 2026')", 
        "limit": "Количество результатов (от 1 до 30, по умолчанию 10)"
    }
)
def web_search(query: str, limit: int = 10) -> str:
    return _web_search(query, limit)

@llm_skill(
    description="Выкачивает текст по конкретному URL, очищает его от мусора и возвращает чистый текст статьи.", 
    parameters={
        "url": "Прямая ссылка на страницу."
    }
)
def read_webpage(url: str) -> str:
    return _read_webpage(url)

@llm_skill(
    description="Получает список свежих статей с главной страницы Хабра (IT-портал).", 
    parameters={
        "limit": "Количество статей (от 1 до 15, по умолчанию 5)"
    }
)
def get_habr_articles(limit: int = 5) -> str:
    return _get_habr_articles(limit)

@llm_skill(
    description="Получает список свежих коротких новостей (инфоповодов) с IT-портала Хабр.", 
    parameters={
        "limit": "Количество новостей (от 1 до 15, по умолчанию 5)"
    }
)
def get_habr_news(limit: int = 5) -> str:
    return _get_habr_news(limit)

@llm_skill(
    description="Композитный навык для глубокого анализа темы. Сам делает поисковые запросы, выкачивает содержимое статей и возвращает единый текст.",
    parameters={
        "queries": "Список поисковых запросов (от 1 до 3).", 
        "max_urls": "Сколько максимум страниц прочитать (по умолчанию 10)."
    }
)
async def deep_research(queries: list, max_urls: int = 10) -> str:
    if not TAVILY_API_KEY:
        return "Ошибка: Ключ TAVILY_API_KEY не найден."
    system_logger.info(f"[Web Search] Запуск Deep Research по запросам: {queries}")
    
    def _get_urls():
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        urls = []
        for q in queries:
            try:
                res = tavily.search(query=q, search_depth="basic", max_results=3)
                for r in res.get('results', []):
                    if r.get('url') not in urls:
                        urls.append(r['url'])
            except Exception as e:
                system_logger.error(f"[Web Search] Tavily ошибка: {e}")
        return urls[:max_urls]
        
    target_urls = await asyncio.to_thread(_get_urls)
    if not target_urls:
        return "Не удалось найти информацию по данным запросам."
        
    system_logger.info(f"[Web Search] Deep Research читает {len(target_urls)} страниц параллельно...")
    read_tasks = [asyncio.to_thread(_read_webpage, url) for url in target_urls]
    pages_content = await asyncio.gather(*read_tasks, return_exceptions=True)
    
    final_report = [f"РЕЗУЛЬТАТЫ DEEP RESEARCH (По запросам: {', '.join(queries)}):\n"]
    for url, content in zip(target_urls, pages_content):
        if isinstance(content, Exception):
            content = f"Ошибка при чтении: {content}"
        final_report.append(f"\nИСТОЧНИК: {url} \n{content}\n")
        
    system_logger.info("[Web Search] deep_research успешно завершен.")
    return "\n".join(final_report)