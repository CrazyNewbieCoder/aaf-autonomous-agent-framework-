import os
import sys
import subprocess
import yaml
from src.cli.colors import G, Y, R, W
from src.cli.setup import get_host_tz

def check_docker():
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception:
        print(f"{R}[X] Docker не запущен или не установлен.{W}")
        sys.exit(1)

def run_cmd(cmd, hide_output=False):
    if hide_output:
        subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        subprocess.run(cmd, shell=True)

def build_sandbox_base(force_rebuild=False):
    """Создает базовый образ внутри изолированного DinD-движка песочницы"""
    image_name = "aaf-sandbox-base:latest"
    
    print(f"{Y}[i] Запуск Sandbox Engine для сборки базового образа.{W}")
    run_cmd("docker compose up -d sandbox_engine", hide_output=True)
    
    import time
    for _ in range(15):
        res = subprocess.run(["docker", "compose", "exec", "sandbox_engine", "docker", "info"], capture_output=True)
        if res.returncode == 0:
            break
        time.sleep(1)
    else:
        print(f"{R}[X] Ошибка: Docker DinD не запустился вовремя.{W}")
        sys.exit(1)

    if not force_rebuild:
        res = subprocess.run(["docker", "compose", "exec", "sandbox_engine", "docker", "images", "-q", image_name], capture_output=True, text=True)
        if res.stdout.strip():
            return 
            
    print(f"{Y}[i] Сборка базового образа песочницы ({image_name}) внутри DinD.{W}")
    dockerfile_content = """
FROM python:3.11-slim
RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    curl \\
    wget \\
    git \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
"""
    os.makedirs("Agents", exist_ok=True)
    temp_df = os.path.join("Agents", "Dockerfile.sandbox.tmp")
    with open(temp_df, "w", encoding="utf-8") as f:
        f.write(dockerfile_content.strip())
        
    try:
        cmd = "mkdir -p /tmp/build && cp /app/Agents/Dockerfile.sandbox.tmp /tmp/build/Dockerfile && cd /tmp/build && docker build -t aaf-sandbox-base:latest ."
        subprocess.run(["docker", "compose", "exec", "sandbox_engine", "sh", "-c", cmd], check=True)
        print(f"{G}[V] Базовый образ песочницы успешно собран.{W}")
    except subprocess.CalledProcessError:
        print(f"{R}[X] Ошибка при сборке базового образа песочницы.{W}")
        sys.exit(1)
    finally:
        if os.path.exists(temp_df):
            os.remove(temp_df)

def generate_docker_compose():
    host_tz = get_host_tz()
    
    compose = {
        "services": {
            "postgres_db": {
                "image": "postgres:15-alpine",
                "restart": "always",
                "environment": {
                    "POSTGRES_USER": "postgres",
                    "POSTGRES_PASSWORD": "postgres",
                    "POSTGRES_DB": "agent_core_db",
                    "TZ": host_tz
                },
                "volumes": ["agent_pg_data:/var/lib/postgresql/data"],
                "healthcheck": {
                    "test": ["CMD-SHELL", "pg_isready -U postgres -d agent_core_db"],
                    "interval": "5s",
                    "timeout": "5s",
                    "retries": 10
                }
            },
            "sandbox_engine": {
                "image": "docker:24-dind",
                "restart": "on-failure",
                "privileged": True,
                "environment": {"DOCKER_TLS_CERTDIR": ""},
                "command": "--host=tcp://0.0.0.0:2375",
                "volumes": ["./Agents:/app/Agents"],
                "healthcheck": {
                    "test": ["CMD", "docker", "info"],
                    "interval": "5s",
                    "timeout": "5s",
                    "retries": 10,
                    "start_period": "5s"
                }
            }
        },
        "volumes": {"agent_pg_data": None}
    }

    agents_dir = "Agents"
    if os.path.exists(agents_dir):
        for agent_name in os.listdir(agents_dir):
            agent_path = os.path.join(agents_dir, agent_name)
            if os.path.isdir(agent_path):
                alias = f"agent_{agent_name.lower()}"
                
                compose["services"][alias] = {
                    "build": {
                        "context": ".",
                        "args": {"AGENT_NAME": agent_name}
                    },
                    "depends_on": {
                        "postgres_db": {"condition": "service_healthy"},
                        "sandbox_engine": {"condition": "service_healthy"}
                    },
                    "restart": "on-failure",
                    "env_file": [f"./Agents/{agent_name}/.env"],
                    "environment": [
                        f"AGENT_NAME={agent_name}",
                        "DOCKER_HOST=tcp://sandbox_engine:2375",
                        f"TZ={host_tz}"
                    ],
                    "networks": {
                        "default": {"aliases": [alias]}
                    },
                    "volumes": [
                        f"./Agents/{agent_name}:/app/Agents/{agent_name}",
                        "./src:/app/src",
                        "./src/layer00_utils/local_models:/app/src/layer00_utils/local_models",
                    ]
                }

    with open("docker-compose.yml", "w", encoding="utf-8") as f:
        f.write("# AUTO-GENERATED BY aaf.py. DO NOT EDIT DIRECTLY.\n")
        f.write("# Используйте `python aaf.py generate` для обновления этого файла.\n\n")
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False, allow_unicode=True)