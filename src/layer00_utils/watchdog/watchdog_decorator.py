import asyncio
import inspect
import time
from functools import wraps
import traceback
from src.layer01_datastate.event_bus.event_bus import event_bus
from src.layer01_datastate.event_bus.events import Events

SYSTEM_MODULE_HEARTBEAT = Events.SYSTEM_MODULE_HEARTBEAT
SYSTEM_MODULE_ERROR = Events.SYSTEM_MODULE_ERROR

# Глобальный словарь для троттлинга ошибок (защита от Broadcast Storm)
_last_error_time = {}

# Все возможные module_name описаны в watchdog.py
def watchdog_decorator(module_name):
    """Публикует событие SYSTEM_MODULE_HEARTBEAT после успешного выполнения функции; 
    В случае ошибки публикует событие SYSTEM_MODULE_ERROR (с защитой от спама)"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Проверяем, асинхронная ли функция
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    # Если синхронная (как ChromaDB), запускаем в отдельном потоке, 
                    # чтобы не стопить весь мозг
                    result = await asyncio.to_thread(func, *args, **kwargs)
                
                await event_bus.publish(SYSTEM_MODULE_HEARTBEAT, module_name=module_name, status="ON")
                return result
            except Exception as e:
                # Получаем последние 3 строчки трейсбека (где именно упало)
                tb = traceback.format_exc(limit=-3)
                error_details = f"{e} \nTraceback:\n{tb}"
                
                # Отправляем CRITICAL агенту не чаще 1 раза в 60 секунд для одного модуля
                now = time.time()
                last_time = _last_error_time.get(module_name, 0)
                
                if now - last_time > 60:
                    _last_error_time[module_name] = now
                    await event_bus.publish(SYSTEM_MODULE_ERROR, module_name=module_name, status="ERROR", error_msg=error_details)
                else:
                    # Если ошибка повторяется, просто пишем в лог консоли, не будя агента
                    from src.layer00_utils.logger import system_logger
                    system_logger.error(f"[WatchDog Muted] Ошибка в {module_name} (скрыто от агента для защиты от спама): {e}")
                
                raise e
        return wrapper
    return decorator

# Пометка: Декораторы отлично работают для функций, которые "сделали дело -> вернули результат" (например, запись в SQL)
# Но для фоновых демонов (демоны слушают микрофон, ждут сообщений в ТГ) декораторы не подходят, потому что демоны никогда не возвращают return
# Поэтому в бесконечных циклах надо публиковать SYSTEM_MODULE_HEARTBEAT вручную, при запуске демона и (по возможности) в процессе работы