# 🧩 Гайд по разработке плагинов для AAF

AAF использует парадигму **Zero-Boilerplate**. Вам не нужно вручную писать громоздкие JSON-схемы для OpenAI Tools или глубоко интегрировать код в ядро. Фреймворк делает это сам через интроспекцию кода.

## 🛠 Как создать свой первый плагин

1. Перейдите в папку вашего агента: `Agents/<NAME>/plugins/`
2. Создайте новый Python-файл, например `crypto_price.py`.
3. Напишите функцию и оберните её в декоратор `@llm_skill`.

### Шаблон плагина:
```python
import asyncio
import os
from src.layer03_brain.agent.skills.auto_schema import llm_skill
from src.layer00_utils.logger import system_logger

@llm_skill(
    description="Узнать текущую цену криптовалюты. Используй при вопросах о рынке.",
    parameters={
        "currency": {
            "description": "Тикер криптовалюты (на английском).", 
            "type": "string",
            "enum": ["btc", "eth", "sol", "ton"] # Жесткие рамки выбора для LLM
        },
        "convert_to": {
            "description": "В какую фиатную валюту конвертировать.",
            "type": "string"
        }
    }
)
async def get_crypto_price(currency: str, convert_to: str = "usd") -> str:
    system_logger.info(f"[Plugin] Запрос цены {currency} в {convert_to}")
    
    # Здесь ваш код (запросы к API, вычисления и т.д.)
    await asyncio.sleep(1) # Имитация задержки
    
    # Инструмент ОБЯЗАН возвращать строку (str)
    return f"Текущая цена {currency.upper()}: 95000 {convert_to.upper()}"
```

## ✨ Как работает магия `@llm_skill`
Декоратор читает аннотации типов вашей функции (`currency: str`) и параметры из `parameters`. Если у аргумента есть значение по умолчанию (например, `convert_to: str = "usd"`), декоратор автоматически помечает его для LLM как **необязательный**. Затем он генерирует валидную схему OpenAI Tools и добавляет функцию в `global_skills_registry`.

## ⚠️ Важное правило: `def` vs `async def`
AAF работает на базе асинхронного Event Loop. 
* **`async def`**: Используйте, если внутри вы используете асинхронные библиотеки (`aiohttp`, `asyncio.sleep`).
* **`def` (Синхронные функции)**: Если вы используете блокирующие библиотеки (например, `requests` или `time.sleep`), объявляйте функцию как обычный `def`. 
**Почему?** Ядро AAF автоматически распознает синхронную функцию и отправит её выполняться в фоновый поток (`asyncio.to_thread`). Это спасет мозг агента от зависания.

## 📦 Сторонние библиотеки
Если вашему плагину нужны внешние библиотеки (например, `web3` или `beautifulsoup4`), просто впишите их в файл:
`Agents/<NAME>/plugins/custom_requirements.txt`

При следующем запуске команды `python aaf.py start <NAME>` Docker автоматически скачает их и пересоберет контейнер агента.