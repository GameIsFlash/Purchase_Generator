import os
import sys
import requests
import tempfile
import subprocess
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading
import time

# ВЕРСИЯ ПРИЛОЖЕНИЯ - автоматически обновляется скриптом релиза
CURRENT_VERSION = "1.0.13"


def check_for_updates():
    """
    Проверяет обновления на GitHub с автоматической установкой
    """
    try:
        global CURRENT_VERSION

        GITHUB_API_URL = "https://api.github.com/repos/GameIsFlash/Purchase_Generator/releases/latest"

        print("Проверка обновлений...")
        response = requests.get(GITHUB_API_URL, timeout=10)

        if response.status_code == 404:
            print("Релизы на GitHub не найдены.")
            return False
        elif response.status_code != 200:
            print(f"Ошибка при проверке обновлений: {response.status_code}")
            return False

        release_info = response.json()
        latest_version = release_info['tag_name'].lstrip('v')

        print(f"Текущая версия: {CURRENT_VERSION}, последняя на GitHub: {latest_version}")

        # Сравниваем версии правильно
        if compare_versions(latest_version, CURRENT_VERSION) > 0:
            print(f"Доступна новая версия: {latest_version}")

            # Ищем установщик в активах релиза
            for asset in release_info['assets']:
                print(f"Найден файл: {asset['name']}")
                if asset['name'] == "PackageGeneratorApp.exe":
                    download_url = asset['browser_download_url']
                    print(f"Найден установщик: {asset['name']}")
                    print(f"URL для скачивания: {download_url}")
                    return download_and_install(download_url, latest_version)

            print("Установщик PackageGeneratorApp.exe не найден в релизе")
            print("Доступные файлы в релизе:")
            for asset in release_info['assets']:
                print(f"  - {asset['name']}")
            return False
        else:
            print("Приложение обновлено до последней версии")
            return False

    except requests.exceptions.Timeout:
        print("Таймаут при проверке обновлений")
        return False
    except requests.exceptions.ConnectionError:
        print("Ошибка соединения при проверке обновлений")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка при проверке обновлений: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_versions(v1, v2):
    """
    Сравнивает две версии
    Возвращает: 1 если v1 > v2, -1 если v1 < v2, 0 если равны
    """

    def normalize(v):
        return [int(x) for x in v.split('.')]

    v1_parts = normalize(v1)
    v2_parts = normalize(v2)

    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = v1_parts[i] if i < len(v1_parts) else 0
        v2_part = v2_parts[i] if i < len(v2_parts) else 0

        if v1_part > v2_part:
            return 1
        elif v1_part < v2_part:
            return -1

    return 0


def download_and_install(download_url, new_version):
    """
    Скачивает и устанавливает обновление с прогресс-баром
    """
    try:
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "PackageGeneratorApp_Update.exe")
        batch_script_path = os.path.join(temp_dir, "update_launcher.bat")

        # Создаем окно прогресса
        progress_window = tk.Tk()
        progress_window.title(f"Установка обновления v{new_version}")
        progress_window.geometry("450x200")
        progress_window.resizable(False, False)
        progress_window.configure(bg='white')

        # Убираем кнопку закрытия
        progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

        # Центрируем окно
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() - progress_window.winfo_width()) // 2
        y = (progress_window.winfo_screenheight() - progress_window.winfo_height()) // 2
        progress_window.geometry(f"+{x}+{y}")

        # Элементы интерфейса
        title_label = tk.Label(
            progress_window,
            text=f"Обнаружено обновление v{new_version}",
            font=("Arial", 12, "bold"),
            bg='white'
        )
        title_label.pack(pady=15)

        label = tk.Label(
            progress_window,
            text="Автоматическая установка обновления...",
            font=("Arial", 10),
            bg='white'
        )
        label.pack(pady=5)

        progress_bar = ttk.Progressbar(
            progress_window,
            orient=tk.HORIZONTAL,
            length=350,
            mode='determinate'
        )
        progress_bar.pack(pady=15)

        status_label = tk.Label(
            progress_window,
            text="Подготовка к скачиванию...",
            font=("Arial", 9),
            bg='white'
        )
        status_label.pack(pady=5)

        info_label = tk.Label(
            progress_window,
            text="Приложение будет автоматически перезапущено после установки",
            font=("Arial", 8),
            fg="gray",
            bg='white'
        )
        info_label.pack(pady=5)

        progress_window.update()

        # Скачиваем установщик с прогресс-баром
        print(f"Скачивание с: {download_url}")
        status_label.config(text="Подключение к серверу...")
        progress_window.update()

        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        status_label.config(text="Скачивание обновления...")
        progress_window.update()

        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # Обновляем прогресс-бар
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        progress_bar['value'] = progress
                        mb_downloaded = downloaded_size / 1024 / 1024
                        mb_total = total_size / 1024 / 1024
                        status_label.config(
                            text=f"Скачано: {mb_downloaded:.1f} MB / {mb_total:.1f} MB ({progress:.0f}%)"
                        )
                        progress_window.update()

        progress_bar['value'] = 100
        status_label.config(text="Скачивание завершено! Запуск установки...")
        progress_window.update()

        # Создаем BAT-скрипт для автоматического обновления
        current_exe = sys.executable
        app_name = os.path.basename(current_exe)

        batch_script = f"""@echo off
chcp 65001 >nul
echo Подготовка к обновлению...
timeout /t 2 /nobreak >nul

REM Закрываем приложение
taskkill /f /im "{app_name}" >nul 2>&1
timeout /t 3 /nobreak >nul

REM Запускаем установщик
echo Установка обновления...
start /wait "" "{installer_path}" /SILENT /NORESTART

REM Ждём завершения установки
timeout /t 5 /nobreak >nul

REM Удаляем временные файлы
del "{installer_path}" >nul 2>&1

REM Запускаем обновлённое приложение
echo Запуск обновлённого приложения...
start "" "%ProgramFiles%\\PackageGeneratorApp\\PurchaseGenerator.exe"

REM Удаляем сам скрипт
del "%~f0" >nul 2>&1
exit
"""

        with open(batch_script_path, 'w', encoding='utf-8') as bat_file:
            bat_file.write(batch_script)

        print("Запуск скрипта обновления...")

        # Запускаем BAT-скрипт
        subprocess.Popen(
            [batch_script_path],
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Закрываем приложение
        time.sleep(2)
        sys.exit(0)

    except Exception as e:
        print(f"Ошибка при установке обновления: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_updates_async():
    """
    Проверяет обновления в фоновом потоке
    """

    def check():
        # Даем основному приложению время запуститься
        time.sleep(3)
        check_for_updates()

    thread = threading.Thread(target=check, daemon=True)
    thread.start()


def main():
    """
    Основная функция приложения
    """
    # Создаем скрытое окно для диалогов обновления
    root = tk.Tk()
    root.withdraw()

    # Проверяем обновления асинхронно
    check_updates_async()

    # Закрываем временное окно
    root.after(1000, root.destroy)
    root.mainloop()

    # Запускаем основное приложение
    try:
        from ui.main_window import main as ui_main
        ui_main()
    except ImportError as e:
        print(f"Ошибка импорта UI: {e}")
        input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()