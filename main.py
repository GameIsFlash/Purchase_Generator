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
        # Текущая версия приложения (меняй при каждом обновлении!)
        CURRENT_VERSION = "1.0.1"

        # URL твоего GitHub репозитория
        GITHUB_API_URL = "https://api.github.com/repos/GameIsFlash/Purchase_Generator/releases/latest"

        print("Проверка обновлений...")
        response = requests.get(GITHUB_API_URL)

        if response.status_code == 200:
            release_info = response.json()
            latest_version = release_info['tag_name']

            if latest_version != CURRENT_VERSION:
                # Показываем диалоговое окно с предложением обновиться
                update_choice = messagebox.askyesno(
                    "Доступно обновление",
                    f"Доступна новая версия {latest_version}. Установить обновление?\n\nПриложение закроется для установки."
                )

                if update_choice:
                    # Ищем установщик в активах релиза
                    for asset in release_info['assets']:
                        if "PackageGeneratorApp_Setup" in asset['name'] and asset['name'].endswith('.exe'):
                            return download_and_install(asset['browser_download_url'])
                else:
                    # Пользователь отказался от обновления
                    messagebox.showinfo("Обновление", "Вы можете обновиться позже через меню помощи.")

        return False

    except Exception as e:
        print(f"Ошибка при проверке обновлений: {e}")
        # Не показываем ошибку пользователю, чтобы не мешать работе
        return False


def download_and_install(download_url):
    """
    Скачивает и устанавливает обновление
    """
    try:
        # Временная папка для загрузки
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "PackageGeneratorApp_Update.exe")

        # Показываем уведомление о начале загрузки
        messagebox.showinfo("Обновление", "Начинается загрузка обновления...")

        print("Скачивание обновления...")
        response = requests.get(download_url, stream=True)

        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print("Запуск установщика обновления...")
        # Запускаем установщик с тихими параметрами
        subprocess.Popen([installer_path, '/SILENT', '/NORESTART'])

        # Закрываем текущее приложение
        messagebox.showinfo("Обновление", "Обновление устанавливается. Приложение закроется.")
        sys.exit(0)

    except Exception as e:
        print(f"Ошибка при установке обновления: {e}")
        messagebox.showerror("Ошибка", f"Не удалось установить обновление: {e}")
        return False


def main():
    """
    Основная функция приложения
    """
    # Сначала проверяем обновления (в фоновом режиме)
    # Для GUI приложений лучше запускать проверку через 1-2 секунды после старта
    root = tk.Tk()
    root.withdraw()  # Скрываем основное окно

    # Запускаем проверку обновлений
    check_for_updates()

    # Закрываем временное окно и запускаем основное приложение
    root.destroy()

    # Запускаем основное приложение
    from ui.main_window import main as ui_main
    ui_main()


if __name__ == "__main__":
    main()