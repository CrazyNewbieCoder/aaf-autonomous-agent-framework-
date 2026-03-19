import os
import shutil
import yaml
from src.cli.colors import G, Y, R, C, W
from src.cli.docker import generate_docker_compose, check_docker, run_cmd

def recursive_merge(template_dict, target_dict):
    is_modified = False
    for key, value in template_dict.items():
        if key not in target_dict:
            target_dict[key] = value
            is_modified = True
        elif isinstance(value, dict) and isinstance(target_dict[key], dict):
            if recursive_merge(value, target_dict[key]):
                is_modified = True
    return is_modified

def patch_agent_configs(agent_target: str):
    agents_to_patch = []
    if agent_target.lower() == "all":
        if os.path.exists("Agents"):
            agents_to_patch = [d for d in os.listdir("Agents") if os.path.isdir(os.path.join("Agents", d))]
    else:
        agents_to_patch = [agent_target.upper()]

    template_path = os.path.join("templates", "settings.yaml")
    if not os.path.exists(template_path):
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_data = yaml.safe_load(f)

    for agent in agents_to_patch:
        target_path = os.path.join("Agents", agent, "config", "settings.yaml")
        if not os.path.exists(target_path):
            continue

        with open(target_path, "r", encoding="utf-8") as f:
            target_data = yaml.safe_load(f)

        if target_data is None:
            target_data = {}

        if recursive_merge(template_data, target_data):
            print(f"{Y}[i] Конфигурация агента '{agent}' автоматически обновлена.{W}")
            with open(target_path, "w", encoding="utf-8") as f:
                yaml.dump(target_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def print_agent_setup_guide(name):
    print(f"\n{G}=================================================={W}")
    print(f"{G}      🚀 ПРОФИЛЬ {name.upper()} ГОТОВ К НАСТРОЙКЕ {W}")
    print(f"{G}=================================================={W}")
    print(f"{Y}[!] ШАГ 1: API КЛЮЧИ И МОДЕЛИ{W}")
    print(f"    Отредактируйте: {C}Agents/{name}/.env{W}")
    print(f"\n{Y}[!] ШАГ 2: АВТОРИЗАЦИЯ ТЕЛЕГРАМ{W}")
    print(f"    Выполните: {C}python aaf.py auth {name}{W}") 
    print(f"\n{Y}[!] ШАГ 3: КОНФИГУРАЦИЯ СИСТЕМЫ{W}")
    print(f"    Файл: {C}Agents/{name}/config/settings.yaml{W}")
    print(f"\n{Y}[!] ШАГ 4: PERSONALITY PROMPT{W}")
    print(f"    Файл: {C}Agents/{name}/config/personality/*.md{W}")
    print(f"\n{Y}[!] ШАГ 5: ЗАПУСК{W}")
    print(f"    Команда: {C}python aaf.py start {name}{W}")
    print(f"{G}=================================================={W}\n")

def create_agent(name: str):
    name = name.upper()
    agent_dir = os.path.join("Agents", name)
    
    if os.path.exists(agent_dir):
        print(f"{R}[X] Ошибка: Агент с именем '{name}' уже существует.{W}")
        return

    print(f"{C}=== Создание профиля агента '{name}' ==={W}")
    
    os.makedirs(os.path.join(agent_dir, "config/personality"), exist_ok=True)
    os.makedirs(os.path.join(agent_dir, "workspace/_data/telegram_sessions"), exist_ok=True)
    os.makedirs(os.path.join(agent_dir, "workspace/temp"), exist_ok=True)
    os.makedirs(os.path.join(agent_dir, "workspace/sandbox"), exist_ok=True)
    os.makedirs(os.path.join(agent_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(agent_dir, "plugins"), exist_ok=True)

    def copy_template(src_rel_path, dest_abs_path, replace_name=False):
        src_path = os.path.join("templates", src_rel_path)
        if not os.path.exists(src_path):
            print(f"{Y}[!] Внимание: Шаблон '{src_path}' не найден.{W}")
            return
        with open(src_path, "r", encoding="utf-8") as f:
            content = f.read()
        if replace_name:
            content = content.replace("{agent_name}", name)
        with open(dest_abs_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    copy_template("env.template", os.path.join(agent_dir, ".env"))
    copy_template("settings.yaml", os.path.join(agent_dir, "config/settings.yaml"), replace_name=True)
    copy_template("agent_sdk.py", os.path.join(agent_dir, "workspace/sandbox/agent_sdk.py"))
    
    with open(os.path.join(agent_dir, "plugins/__init__.py"), "w", encoding="utf-8") as f:
        f.write("")
    copy_template("example_plugin.py", os.path.join(agent_dir, "plugins/example_plugin.py"))
    with open(os.path.join(agent_dir, "plugins/custom_requirements.txt"), "w", encoding="utf-8") as f:
        f.write("# Впишите сюда библиотеки для ваших плагинов\n")

    for md_file in ["SOUL.md", "COMMUNICATION_STYLE.md", "EXAMPLES_OF_STYLE.md"]:
        copy_template(f"personality/{md_file}", os.path.join(agent_dir, f"config/personality/{md_file}"))

    generate_docker_compose()
    print_agent_setup_guide(name=name)

def cmd_delete(agent_name: str):
    agent_name = agent_name.upper()
    agent_dir = os.path.join("Agents", agent_name)
    
    if not os.path.exists(agent_dir):
        print(f"{R}[X] Ошибка: Профиль агента '{agent_name}' не найден.{W}")
        return
        
    print(f"\n{Y}Инициализация процедуры удаления профиля '{agent_name}'.{W}")
    ans1 = input(f"{C}Подтверждаете полное удаление директории и данных? [y/N]: {W}").strip().lower()
    if ans1 not in ['y', 'yes', 'д', 'да']:
        print(f"{G}Операция отменена.{W}")
        return

    print(f"{Y}Вам совсем не жалко этот алгоритм?{W}")
    ans2 = input(f"{C}Окончательно отправляем '{agent_name}' в цифровой Лимб? [y/N]: {W}").strip().lower()
    
    if ans2 not in ['y', 'yes', 'д', 'да']:
        print(f"{G}Агент '{agent_name}' спасен. Возвращаемся к работе.{W}")
        return

    alias = f"agent_{agent_name.lower()}"
    if check_docker():
        run_cmd(f"docker compose stop {alias}", hide_output=True)
        run_cmd(f"docker compose rm -f {alias}", hide_output=True)

    try:
        shutil.rmtree(agent_dir)
        print(f"{G}[V] Директория '{agent_dir}' успешно уничтожена.{W}")
    except Exception as e:
        print(f"{R}[X] Ошибка при удалении папки: {e}{W}")

    generate_docker_compose()
    print(f"{G}[V] docker-compose.yml пересобран.{W}")