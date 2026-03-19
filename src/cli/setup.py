import os
import sys
import subprocess
from src.cli.colors import G, Y, W

def get_host_tz():
    import time
    is_dst = time.daylight and time.localtime().tm_isdst > 0
    offset_sec = time.altzone if is_dst else time.timezone
    offset_hours = offset_sec / 3600.0
    
    if offset_hours.is_integer():
        offset_str = f"{int(offset_hours):+d}"
    else:
        hours = int(offset_hours)
        minutes = int(abs(offset_hours - hours) * 60)
        sign = "+" if offset_hours >= 0 else "-"
        offset_str = f"{sign}{abs(hours)}:{minutes:02d}"
        
    return f"HOST{offset_str}"

def check_and_download_models():
    model_path = os.path.join("src", "layer00_utils", "local_models", "models--BAAI--bge-m3")
    if not os.path.exists(model_path):
        print(f"{Y}[!] Embedding модель не найдена. Инициализация загрузки (~2.5 ГБ).{W}")
        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            print(f"{Y}Устанавливаю huggingface_hub...{W}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
            from huggingface_hub import snapshot_download
        
        snapshot_download(
            repo_id="BAAI/bge-m3",
            local_dir=os.path.join("src", "layer00_utils", "local_models", "models--BAAI--bge-m3"),
            local_dir_use_symlinks=False
        )
        print(f"{G}[V] Embedding модель успешно загружена.{W}")