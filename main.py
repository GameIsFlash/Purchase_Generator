import os
import sys
import requests
import tempfile
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path


def check_for_updates():
    """
    Проверяет обновления на GitHub с GUI-диалогами
    """
    try:
        CURRENT_VERSION = "1.0.0"  # Автоматически обновляется батником

        GITHUB_API_URL = "https://api.github.com/repos/GameIsFlash/Purchase_Generator/releases/latest"

        print("Проверка обновлений...")
        response = requests.get(GITHUB_API_URL, timeout=10)

        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info['tag_name'].lstrip('v')

            if latest_version != CURRENT_VERSION:
                update_choice = messagebox.askyesno(
                    "Доступно обновление",
                    f"Доступна новая версия {latest_version}. Установить обновление?\n\nПриложение закроется для установки."
                )

                if update_choice:
                    for asset in release_info['assets']:
                        if "PackageGeneratorApp_Setup" in asset['name'] and asset['name'].endswith('.exe'):
                            return download_and_install(asset['browser_download_url'])

        return False

    except Exception as e:
        print(f"Ошибка при проверке обновлений: {e}")
        return False


def download_and_install(download_url):
    """
    Скачивает и устанавливает обновление с принудительным закрытием
    """
    try:
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "PackageGeneratorApp_Update.exe")
        batch_script_path = os.path.join(temp_dir, "update_launcher.bat")

        messagebox.showinfo("Обновление", "Скачивание обновления...")

        # Скачиваем установщик
        response = requests.get(download_url, stream=True, timeout=30)
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Создаем BAT-скрипт для обновления
        batch_script = f"""
@echo off
chcp 65001 >nul
echo Закрытие приложения для обновления...
timeout /t 3 /nobreak >nul
taskkill /f /im "PurchaseGenerator.exe" >nul 2>&1
timeout /t 2 /nobreak >nul
echo Запуск установщика обновления...
"{{installer_path}}" /SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
echo Удаление временных файлов...
del "{{batch_script_path}}"
exit
""".replace("{{installer_path}}", installer_path).replace("{{batch_script_path}}", batch_script_path)

        with open(batch_script_path, 'w', encoding='utf-8') as bat_file:
            bat_file.write(batch_script)

        # Запускаем BAT-скрипт
        subprocess.Popen([batch_script_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

        # Закрываем текущее приложение
        sys.exit(0)

    except Exception as e:
        print(f"Ошибка при установке обновления: {e}")
        messagebox.showerror("Ошибка", f"Не удалось установить обновление: {e}")
        return False


def main():
    """
    Основная функция приложения
    """
    # Создаем скрытое окно для диалогов обновления
    root = tk.Tk()
    root.withdraw()

    # Проверяем обновления
    check_for_updates()

    # Закрываем временное окно
    root.destroy()

    # Запускаем основное приложение
    from ui.main_window import main as ui_main
    ui_main()


if __name__ == "__main__":
    main()