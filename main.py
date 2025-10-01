import os
import sys
import requests
import tempfile
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# ВЕРСИЯ ПРИЛОЖЕНИЯ - автоматически обновляется скриптом релиза
CURRENT_VERSION = "1.0.8"


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

        if latest_version != CURRENT_VERSION:
            # Ищем установщик в активах релиза - ИСПРАВЛЕНО ИМЯ ФАЙЛА
            for asset in release_info['assets']:
                if asset['name'] == "PackageGeneratorApp.exe":
                    download_url = asset['browser_download_url']
                    print(f"Найден установщик: {asset['name']}")
                    return download_and_install(download_url, latest_version)

            print("Установщик не найден в релизе")
            # Дополнительная диагностика
            print("Доступные файлы в релизе:")
            for asset in release_info['assets']:
                print(f"  - {asset['name']}")

            messagebox.showerror("Ошибка",
                                 f"Установщик не найден в последнем релизе на GitHub\n\n"
                                 f"Доступные файлы:\n" +
                                 "\n".join([f"• {asset['name']}" for asset in release_info['assets']]))
            return False

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


def download_and_install(download_url, new_version):
    """
    Скачивает и устанавливает обновление с прогресс-баром
    """
    try:
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "PackageGeneratorApp_Update.exe")
        batch_script_path = os.path.join(temp_dir, "update_launcher.bat")

        # Создаем окно прогресса
        progress_window = tk.Toplevel()
        progress_window.title(f"Обновление до v{new_version}")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient()  # Поверх главного окна
        progress_window.grab_set()  # Модальное

        # Центрируем окно
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() - progress_window.winfo_width()) // 2
        y = (progress_window.winfo_screenheight() - progress_window.winfo_height()) // 2
        progress_window.geometry(f"+{x}+{y}")

        # Элементы интерфейса
        label = tk.Label(progress_window, text="Скачивание обновления...", font=("Arial", 10))
        label.pack(pady=10)

        progress_bar = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL,
                                       length=300, mode='determinate')
        progress_bar.pack(pady=10)

        status_label = tk.Label(progress_window, text="Подготовка...", font=("Arial", 8))
        status_label.pack(pady=5)

        progress_window.update()

        # Скачиваем установщик с прогресс-баром
        print(f"Скачивание с: {download_url}")
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # Обновляем прогресс-бар
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        progress_bar['value'] = progress
                        status_label.config(
                            text=f"Скачано: {downloaded_size // 1024 // 1024} MB / {total_size // 1024 // 1024} MB ({progress:.1f}%)"
                        )
                        progress_window.update()

        progress_bar['value'] = 100
        status_label.config(text="Скачивание завершено! Запуск установки...")
        progress_window.update()

        # Даем пользователю немного увидеть завершение
        progress_window.after(1000, progress_window.destroy)
        progress_window.update()

        print("Установщик скачан, создание скрипта обновления...")

        # Создаем BAT-скрипт для обновления
        batch_script = f"""
@echo off
chcp 65001 >nul
echo Закрытие приложения для обновления...
timeout /t 2 /nobreak >nul
taskkill /f /im "PurchaseGenerator.exe" >nul 2>&1
timeout /t 1 /nobreak >nul
echo Запуск установщика обновления...
start "" "{installer_path}" /SILENT
echo Удаление временных файлов...
timeout /t 3 /nobreak >nul
del "{installer_path}" >nul 2>&1
del "%~f0" >nul 2>&1
exit
"""

        with open(batch_script_path, 'w', encoding='utf-8') as bat_file:
            bat_file.write(batch_script)

        # Запускаем BAT-скрипт
        subprocess.Popen([batch_script_path], shell=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)

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

    # Проверяем обновления (автоматически, без вопросов)
    check_for_updates()

    # Закрываем временное окно
    root.destroy()

    # Запускаем основное приложение
    from ui.main_window import main as ui_main
    ui_main()


if __name__ == "__main__":
    main()