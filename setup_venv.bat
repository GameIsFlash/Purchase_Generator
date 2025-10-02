@echo off
chcp 65001 >nul

echo.
echo ========================================
echo    НАСТРОЙКА VIRTUAL ENVIRONMENT
echo ========================================
echo.

set "REPO_PATH=%~dp0"

cd /d "%REPO_PATH%"

echo Создание виртуального окружения...
python -m venv .venv

echo Активация виртуального окружения...
call .venv\Scripts\activate.bat

echo Установка зависимостей...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo ✓ Виртуальное окружение настроено!
echo.
echo Для активации в будущем используйте:
echo   .venv\Scripts\activate.bat
echo.
pause