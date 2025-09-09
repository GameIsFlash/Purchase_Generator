import subprocess
import platform
from pathlib import Path

def open_folder(folder_path: str):
    """Открыть папку в проводнике ОС"""
    try:
        folder = Path(folder_path).resolve()
        if not folder.exists():
            return False

        system = platform.system()
        if system == "Windows":
            import os
            os.startfile(folder)
        elif system == "Darwin":
            subprocess.run(["open", str(folder)], check=True)
        else:
            subprocess.run(["xdg-open", str(folder)], check=True)
        return True
    except Exception as e:
        print(f"Ошибка открытия папки: {e}")
        return False