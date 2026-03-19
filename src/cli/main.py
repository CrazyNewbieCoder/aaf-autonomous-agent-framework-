import sys
import os
import argparse
import shlex
import subprocess

from src.cli.colors import G, Y, R, C, W
from src.cli.setup import check_and_download_models
from src.cli.docker import check_docker, build_sandbox_base, generate_docker_compose, run_cmd
from src.cli.agent import patch_agent_configs, create_agent, cmd_delete
from src.cli.auth import cmd_auth
from src.cli.status import cmd_status, cmd_logs

def process_command(args_list):
    parser = argparse.ArgumentParser(description="AAF Swarm Manager (v1.2.0)", exit_on_error=False)
    parser.add_argument("command", choices=["status", "create", "auth", "start", "stop", "restart", "rebuild", "delete", "logs", "generate", "help", "exit", "quit"], help="Команда для выполнения")
    parser.add_argument("agent", nargs="?", help="Имя агента (или 'all')")
    
    try:
        args = parser.parse_args(args_list)
    except SystemExit:
        return True
    
    if args.command in ["exit", "quit"]:
        return False
        
    if args.command == "help":
        print(f"\n{C}Доступные команды:{W}")
        print(f"  {G}status{W}               - Показать статус всех агентов")
        print(f"  {G}create <NAME>{W}        - Создать профиль нового агента")
        print(f"  {G}auth <NAME>{W}          - Авторизовать Telegram для агента")
        print(f"  {G}start <NAME | all>{W}   - Запустить агента (или всех)")
        print(f"  {G}stop <NAME | all>{W}    - Остановить агента (или всех)")
        print(f"  {G}restart <NAME | all>{W} - Перезапустить агента (или всех)")
        print(f"  {G}rebuild <NAME | all>{W} - Чистая пересборка (без кэша Docker)")
        print(f"  {G}delete <NAME>{W}        - Полностью удалить профиль агента")
        print(f"  {G}logs <NAME>{W}          - Смотреть логи агента в реальном времени")
        print(f"  {G}generate{W}             - Пересобрать docker-compose.yml")
        print(f"  {G}exit{W}                 - Выйти из AAF Manager\n")
        return True

    if args.command == "status":
        cmd_status()
        
    elif args.command == "generate":
        generate_docker_compose()
        print(f"{G}[V] docker-compose.yml пересобран.{W}")

    elif args.command == "create":
        if not args.agent:
            print(f"{R}Укажите имя агента: create <NAME>{W}")
            return True
        create_agent(args.agent)

    elif args.command == "auth":
        if not args.agent:
            print(f"{R}Укажите имя агента: auth <NAME>{W}")
            return True
        cmd_auth(args.agent)

    elif args.command == "start":
        check_and_download_models()
        check_docker()

        agent_target = args.agent if args.agent else "all"
        patch_agent_configs(agent_target)

        # Сначала генерируем compose, чтобы появился sandbox_engine
        generate_docker_compose()
        # Потом собираем базовый образ внутри песочницы
        build_sandbox_base(force_rebuild=False)

        if not args.agent or args.agent.lower() == "all":
            print(f"{Y}Запуск всей инфраструктуры и агентов.{W}")
            run_cmd("docker compose up -d --build")
        else:
            alias = f"agent_{args.agent.lower()}"
            print(f"{C}Запуск агента {args.agent.upper()}.{W}")
            run_cmd(f"docker compose up -d --build {alias}")

    elif args.command == "stop":
        check_docker()
        if not args.agent or args.agent.lower() == "all":
            print(f"{Y}Остановка всей системы.{W}")
            run_cmd("docker compose down")
        else:
            alias = f"agent_{args.agent.lower()}"
            print(f"{Y}Остановка агента {args.agent.upper()}.{W}")
            run_cmd(f"docker compose stop {alias}")

            agents_dir = "Agents"
            if os.path.exists(agents_dir):
                agents = [d for d in os.listdir(agents_dir) if os.path.isdir(os.path.join(agents_dir, d))]
                result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
                running_names = [name for name in result.stdout.strip().split('\n') if name]
                
                any_agent_running = any(any(f"agent_{ag.lower()}" in name for name in running_names) for ag in agents)
                        
                if not any_agent_running:
                    print(f"\n{C}[i] В системе больше нет активных агентов.{W}")
                    print(f"{Y}Автоматическая остановка PostgreSQL и Sandbox.{W}")
                    run_cmd("docker compose stop")

    elif args.command == "restart":
        check_docker()
        if not args.agent or args.agent.lower() == "all":
            print(f"{Y}Перезапуск всей системы.{W}")
            run_cmd("docker compose restart")
        else:
            alias = f"agent_{args.agent.lower()}"
            print(f"{Y}Перезапуск агента {args.agent.upper()}.{W}")
            run_cmd(f"docker compose restart {alias}")

    elif args.command == "rebuild":
        check_and_download_models()
        check_docker()

        agent_target = args.agent if args.agent else "all"
        patch_agent_configs(agent_target)
        
        generate_docker_compose()
        build_sandbox_base(force_rebuild=True)

        if not args.agent or args.agent.lower() == "all":
            print(f"{Y}Пересборка всех образов без кэша.{W}")
            run_cmd("docker compose build --no-cache")
            run_cmd("docker compose up -d")
        else:
            alias = f"agent_{args.agent.lower()}"
            print(f"{Y}Принудительная чистая пересборка агента {args.agent.upper()} без кэша.{W}")
            run_cmd(f"docker compose build --no-cache {alias}")
            print(f"{C}Запуск агента {args.agent.upper()}...{W}")
            run_cmd(f"docker compose up -d {alias}")

    elif args.command == "delete":
        if not args.agent:
            print(f"{R}Укажите имя агента: delete <NAME>{W}")
            return True
        cmd_delete(args.agent)

    elif args.command == "logs":
        if not args.agent:
            print(f"{R}Укажите имя агента: logs <NAME>{W}")
            return True
        cmd_logs(args.agent)

    return True

def interactive_mode():
    print(f"{C}========================================{W}")
    print(f"{G}            AAF Manager (v1.2.0)        {W}")
    print(f"{C}========================================{W}")
    print("Введите 'help' для списка команд или 'exit' для выхода.\n")
    
    while True:
        try:
            user_input = input(f"{C}AAF > {W}").strip()
            if not user_input:
                continue
                
            args_list = shlex.split(user_input)
            if not process_command(args_list):
                print(f"{Y}Выход из AAF Manager.{W}")
                break
                
        except KeyboardInterrupt:
            print(f"\n{Y}Выход из AAF Manager.{W}")
            break
        except Exception as e:
            print(f"{R}Ошибка: {e}{W}")

def main():
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        process_command(sys.argv[1:])