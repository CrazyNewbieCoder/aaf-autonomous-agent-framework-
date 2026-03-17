import requests
import os
from datetime import datetime
from src.layer00_utils.logger import system_logger
from collections import deque
import tiktoken

from src.layer00_utils.config_manager import config
from src.layer00_utils.env_manager import load_agent_env

load_agent_env()


CITY_NAME = config.system.weather_city
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

encoding = tiktoken.get_encoding("cl100k_base")

class TokenTracker:
    def __init__(self, maxlen=10):
        self.history = deque(maxlen=maxlen)

    def add_record(self, cycle_type: str, prompt_tokens: int, context_tokens: int, tools_tokens: int = 0) -> str:
        """Записывает токены текущего цикла и возвращает красивую статистику для логов"""
        total = prompt_tokens + context_tokens + tools_tokens
        self.history.append({
            "type": cycle_type,
            "total": total
        })
        
        total_last_n = sum(item["total"] for item in self.history)
        avg_tokens = total_last_n // len(self.history)
        
        return f"Входящих токенов: {total} (Промпт: {prompt_tokens}, Контекст: {context_tokens}, Инструменты: {tools_tokens}). За последние {len(self.history)} вызовов: {total_last_n} токенов (в среднем {avg_tokens}/вызов)."

token_tracker = TokenTracker(maxlen=10)

def count_tokens(text: str) -> int:
    """Возвращает количество токенов для переданной строки."""
    return len(encoding.encode(text))

def get_weather(city_name: str = None):
    """Получает текущую погоду"""
    try:
        if city_name:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
        else: # Если город не передан, узнаем по умолчанию
            url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"

        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return f"Ошибка погоды: API вернул код {response.status_code} ({response.json().get('message', 'Нет деталей')})"
        
        weather_data = response.json()

        city_name = weather_data["name"]
        weather = weather_data["weather"][0]["description"]
        feeling_temp = int(weather_data["main"]["feels_like"])
        temp = int(weather_data["main"]["temp"])
        humidity = int(weather_data["main"]["humidity"])
        wind = weather_data["wind"]["speed"]

        final_answer = f"Город: {city_name}; Погода: {weather}; Ощущается: {feeling_temp}°; Текущая температура: {temp}°; Влажность воздуха: {humidity}; Ветер: {wind} м/с."

        return final_answer
    
    except Exception as e:
        system_logger.error(f"Ошибка при получении погоды: {e}")
        return f"Ошибка при получении погоды: {e}"
    
def get_datetime():
    try:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        system_logger.error(f"Ошибка при получении даты и времени: {e}")