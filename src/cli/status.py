import os
import platform
import subprocess
from src.cli.colors import G, R, C, W, Y
from src.cli.docker import check_docker, run_cmd

def cmd_status():
    check_docker()
    print(f"\n{C}=== AAF Status ==={W}")
    
    agents = [d for d in os.listdir("Agents") if os.path.isdir(os.path.join("Agents", d))] if os.path.exists("Agents") else []
    if not agents:
        print("Агенты не найдены. Используйте 'python aaf.py create <NAME>'.")
        return
        
    result = subprocess.run(["docker", "ps", "--format", "{{.Names}}|{{.Status}}"], capture_output=True, text=True)
    running_containers = {line.split('|')[0]: line.split('|')[1] for line in result.stdout.strip().split('\n') if line}
    
    print(f"{'AGENT NAME':<15} | {'STATUS':<20} | {'LLM MODEL':<25}")
    print("-" * 65)
    
    for agent in agents:
        alias = f"agent_{agent.lower()}"
        status = f"{R}Offline{W}"
        for container_name, container_status in running_containers.items():
            if alias in container_name:
                status = container_status
                break
                
        if "Up" in status:
            status = f"{G}{status}{W}"
            
        model = "Unknown"
        settings_path = os.path.join("Agents", agent, "config/settings.yaml")
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith("model_name:"):
                        model = line.split(":")[1].strip().replace('"', '').replace("'", "")
                        break
                        
        print(f"{agent:<15} | {status:<29} | {C}{model:<25}{W}")
    print("\n")

def cmd_logs(agent_name: str):
    check_docker()
    alias = f"agent_{agent_name.lower()}"
    print(f"{G}Логи агента {agent_name} открыты в новом окне.{W}")
    
    current_os = platform.system()
    
    if current_os == "Windows":
        subprocess.Popen(f'start "AAF Logs: {agent_name.upper()}" cmd /k "docker compose logs {alias} -f"', shell=True)
    elif current_os == "Darwin":
        subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "cd {os.getcwd()} && docker compose logs {alias} -f"'])
    else:
        try:
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'docker compose logs {alias} -f; exec bash'])
        except Exception:
            print(f"{Y}Не удалось открыть новое окно терминала. Логи запущены здесь (Нажмите Ctrl+C для выхода).{W}")
            try:
                run_cmd(f"docker compose logs {alias} -f")
            except KeyboardInterrupt:
                print(f"\n{C}Выход из просмотра логов.{W}")