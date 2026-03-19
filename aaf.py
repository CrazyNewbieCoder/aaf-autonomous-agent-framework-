import sys
import subprocess

# Базовая проверка зависимостей до импорта внутренних модулей
try:
    import yaml
except ImportError:
    print("\033[93mУстановка PyYAML.\033[0m")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"])
    import yaml  # noqa: F401

from src.cli.main import main

if __name__ == "__main__":
    main()