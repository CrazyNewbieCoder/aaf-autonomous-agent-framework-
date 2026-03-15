from pathlib import Path
from src.layer00_utils.logger import system_logger

# Единый менеджер
from src.layer00_utils.env_manager import AGENT_NAME

class PromptManager:
    """Хранилище и сборка общих промптов из .md файлов"""
    def __init__(self):
        # Определяем абсолютный путь к папке prompt/ (здесь лежат системные инструкции)
        self.system_dir = Path(__file__).resolve().parent
        
        # Поднимаемся на 4 уровня вверх до корня проекта
        self.project_root = self.system_dir.parents[3]
        
        # ДИНАМИЧЕСКИЙ ПУТЬ К ЛИЧНОСТИ (Agents/{AGENT_NAME}/config/personality)
        self.personality_dir = self.project_root / "Agents" / AGENT_NAME / "config" / "personality"

        # Загружаем личность (из конфига конкретного агента)
        self.SOUL = self._load_file(self.personality_dir / "SOUL.md")
        self.COMMUNICATION_STYLE = self._load_file(self.personality_dir / "COMMUNICATION_STYLE.md")
        self.EXAMPLES_OF_STYLE = self._load_file(self.personality_dir / "EXAMPLES_OF_STYLE.md")

        # Загружаем системные инструкции (из исходного кода src/ - общие для всех)
        self.SYSTEM_INSTRUCTIONS = self._load_file(self.system_dir / "system" / "SYSTEM_INSTRUCTIONS.md")
        self.PROACTIVITY_INSTRUCTIONS = self._load_file(self.system_dir / "system" / "PROACTIVITY_INSTRUCTIONS.md")
        self.THOUGHTS_INSTRUCTIONS = self._load_file(self.system_dir / "system" / "THOUGHTS_INSTRUCTIONS.md")

    def _load_file(self, full_path: Path) -> str:
        """Читает .md файл как текст"""
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            system_logger.error(f"Ошибка: Файл промпта не найден -> {full_path}")
            return f"[Ошибка: Файл {full_path.name} не найден]"
        except Exception as e:
            system_logger.error(f"Ошибка при чтении {full_path}: {e}")
            return f"[Ошибка чтения файла: {full_path.name}]"

    def build_event_driven_prompt(self, dynamic_traits: str) -> str:
        """Для обычного общения и прямого ответа на события (Event-Driven)"""
        PERSONALITY_PARAMETERS = f"## DYNAMIC PERSONALITY PARAMETERS (Твои приобретенные привычки и правила)\n{dynamic_traits}" if dynamic_traits else ""
        
        prompt_parts = [
            self.SOUL,
            PERSONALITY_PARAMETERS,
            self.SYSTEM_INSTRUCTIONS,
            self.COMMUNICATION_STYLE,
            self.EXAMPLES_OF_STYLE
        ]
        return "\n\n".join(filter(None, prompt_parts))
    
    def build_proactivity_prompt(self, dynamic_traits: str) -> str:
        """Для фоновой активности, выполнения задач и инициативы"""
        PERSONALITY_PARAMETERS = f"## DYNAMIC PERSONALITY PARAMETERS (Твои приобретенные привычки и правила)\n{dynamic_traits}" if dynamic_traits else ""
        
        prompt_parts = [
            self.SOUL,
            PERSONALITY_PARAMETERS,
            self.SYSTEM_INSTRUCTIONS,       
            self.COMMUNICATION_STYLE,       
            self.PROACTIVITY_INSTRUCTIONS
        ]
        return "\n\n".join(filter(None, prompt_parts))
    
    def build_thoughts_prompt(self, dynamic_traits: str) -> str:
        """Для рефлексии, анализа и заполнения векторных баз"""
        PERSONALITY_PARAMETERS = f"## DYNAMIC PERSONALITY PARAMETERS (Твои приобретенные привычки и правила)\n{dynamic_traits}" if dynamic_traits else ""
        
        prompt_parts = [
            self.SOUL,
            PERSONALITY_PARAMETERS,
            self.SYSTEM_INSTRUCTIONS, 
            self.THOUGHTS_INSTRUCTIONS
        ]
        return "\n\n".join(filter(None, prompt_parts))

prompt_manager = PromptManager()

if __name__ == "__main__":
    print(prompt_manager.build_proactivity_prompt(""))