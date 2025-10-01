import os
import sys
import requests
import tempfile
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# ВЕРСИЯ ПРИЛОЖЕНИЯ - автоматически обновляется скриптом релиза
CURRENT_VERSION = "1.0.6"


def check_for_updates():
    """
    Проверяет обновления на GitHub с обработкой отсутствия релизов
    """
    try:
        global CURRENT_VERSION

        GITHUB_API_URL = "https://api.github.com/repos/GameIsFlash/Purchase_Generator/releases/latest"

        print("Проверка обновлений...")
        response = requests.get(GITHUB_API_URL, timeout=10)

        # Если нет релизов (404) или другие ошибки
        if response.status_code == 404:
            print("Релизы на GitHub не найдены. Это нормально для первого запуска.")
            return False
        elif response.status_code != 200:
            print(f"Ошибка при проверке обновлений: {response.status_code}")
            return False

        release_info = response.json()
        latest_version = release_info['tag_name'].lstrip('v')

        print(f"Текущая версия: {CURRENT_VERSION}, последняя на GitHub: {latest_version}")

        if latest_version != CURRENT_VERSION:
            update_choice = messagebox.askyesno(
                "Доступно обновление",
                f"Доступна новая версия {latest_version}. Установить обновление?\n\nПриложение закроется для установки."
            )

            if update_choice:
                # Ищем установщик в активах релиза
                for asset in release_info['assets']:
                    if "PackageGeneratorApp_Setup" in asset['name'] and asset['name'].endswith('.exe'):
                        download_url = asset['browser_download_url']
                        print(f"Найден установщик: {asset['name']}")
                        return download_and_install(download_url)

                print("Установщик не найден в релизе")
                messagebox.showerror("Ошибка", "Установщик не найден в последнем релизе на GitHub")

        return False

    except requests.exceptions.Timeout:
        print("Таймаут при проверке обновлений")
        return False
    except requests.exceptions.ConnectionError:
        print("Ошибка соединения при проверке обновлений")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка при проверке обновлений: {e}")
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
        print(f"Скачивание с: {download_url}")
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print("Установщик скачан, создание скрипта обновления...")

        # Создаем BAT-скрипт для обновления
        batch_script = f"""
@echo off
chcp 65001 >nul
echo Закрытие приложения для обновления...
timeout /t 3 /nobreak >nul
taskkill /f /im "PurchaseGenerator.exe" >nul 2>&1
timeout /t 2 /nobreak >nul
echo Запуск установщика обновления...
"{installer_path}" /SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
echo Удаление временных файлов...
timeout /t 5 /nobreak >nul
del "{installer_path}" >nul 2>&1
del "{batch_script_path}" >nul 2>&1
exit
"""

        with open(batch_script_path, 'w', encoding='utf-8') as bat_file:
            bat_file.write(batch_script)

        # Запускаем BAT-скрипт
        subprocess.Popen([batch_script_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

        # Закрываем текущее приложение
        messagebox.showinfo("Обновление", "Обновление запущено. Приложение закроется.")
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