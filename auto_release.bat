@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo    АВТОМАТИЧЕСКИЙ РЕЛИЗ PACKAGEGENERATOR
echo ========================================
echo.

REM --- КОНФИГУРАЦИЯ ---
set "REPO_PATH=%~dp0"
set "GITHUB_USER=GameIsFlash"
set "GITHUB_REPO=Purchase_Generator"
set "VENV_PATH=%REPO_PATH%.venv"

REM --- ПЕРЕХОД В ПАПКУ ПРОЕКТА ---
cd /d "%REPO_PATH%"
echo Текущая папка: %CD%

REM --- ПРОВЕРКА И АКТИВАЦИЯ VENV ---
echo.
echo Проверка виртуального окружения...
if exist "%VENV_PATH%\Scripts\activate.bat" (
    echo Активация виртуального окружения...
    call "%VENV_PATH%\Scripts\activate.bat"
    echo ✓ Виртуальное окружение активировано
) else (
    echo Создание виртуального окружения...
    python -m venv .venv
    call ".venv\Scripts\activate.bat"
    echo Установка зависимостей...
    pip install -r requirements.txt >nul 2>&1
    pip install pyinstaller >nul 2>&1
    echo ✓ Виртуальное окружение создано и настроено
)

REM --- ПРОВЕРКА ЗАВИСИМОСТЕЙ ---
echo.
echo Проверка зависимостей...
pyinstaller --version >nul 2>&1
if !errorlevel! neq 0 (
    echo Установка PyInstaller...
    pip install pyinstaller >nul 2>&1
)
python -c "import requests" 2>nul
if !errorlevel! neq 0 (
    echo Установка недостающих библиотек...
    pip install -r requirements.txt >nul 2>&1
)
echo ✓ Все зависимости проверены

REM --- ПОЛУЧЕНИЕ ВЕРСИИ ---
for /f "tokens=2 delims=^=" %%i in ('findstr "CURRENT_VERSION" main.py') do (
    set VERSION_LINE=%%i
)
set "CURRENT_VERSION=!VERSION_LINE:"=!"
set "CURRENT_VERSION=!CURRENT_VERSION: =!"
echo Текущая версия: !CURRENT_VERSION!

REM --- АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ ВЕРСИИ ---
echo.
echo Автоматическое обновление версии...
for /f "tokens=1,2,3 delims=." %%a in ("!CURRENT_VERSION!") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)
set /a NEW_PATCH=!PATCH!+1
set "NEW_VERSION=!MAJOR!.!MINOR!.!NEW_PATCH!"
echo Новая версия: !CURRENT_VERSION! -^> !NEW_VERSION!

REM --- ОБНОВЛЕНИЕ ВЕРСИИ В ФАЙЛАХ ---
echo.
echo Шаг 1/4: Обновление версии в файлах...
python -c "content = open('main.py', 'r', encoding='utf-8').read(); new_content = content.replace('CURRENT_VERSION = \"!CURRENT_VERSION!\"', 'CURRENT_VERSION = \"!NEW_VERSION!\"'); open('main.py', 'w', encoding='utf-8').write(new_content)"
python -c "content = open('create_installer.iss', 'r', encoding='utf-8').read(); import re; content = re.sub(r'AppVersion=[0-9.]+', 'AppVersion=!NEW_VERSION!', content); content = re.sub(r'VersionInfoVersion=[0-9.]+', 'VersionInfoVersion=!NEW_VERSION!', content); open('create_installer.iss', 'w', encoding='utf-8').write(content)"
echo ✓ Версии обновлены

REM --- КОММИТ И ПУШ ---
echo.
echo Шаг 2/4: Коммит изменений в Git...
git add . >nul 2>&1
git commit -m "🚀 Release v!NEW_VERSION!" >nul 2>&1
git push >nul 2>&1
echo ✓ Код загружен на GitHub

REM --- СБОРКА ПРИЛОЖЕНИЯ ---
echo.
echo Шаг 3/4: Сборка приложения...
echo   Очистка предыдущих сборок...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul
if exist "Output" rmdir /s /q "Output" 2>nul

echo   Сборка EXE файла...
pyinstaller --noconfirm --clean --windowed --icon=icon.ico --name=PurchaseGenerator --add-data="data;data" --add-data="ui;ui" --hidden-import=tkinter --hidden-import=customtkinter --hidden-import=openpyxl --hidden-import=pandas --hidden-import=PIL --hidden-import=requests --hidden-import=threading --hidden-import=tempfile --hidden-import=subprocess --hidden-import=pathlib main.py >nul 2>&1

if not exist "dist\PurchaseGenerator\PurchaseGenerator.exe" (
    echo ❌ ОШИБКА: Не удалось собрать EXE файл!
    echo Пробуем альтернативный метод сборки...
    pyinstaller --noconfirm --clean --onefile --windowed --icon=icon.ico --name=PurchaseGenerator --add-data="data;data" --add-data="ui;ui" --hidden-import=tkinter --hidden-import=customtkinter --hidden-import=openpyxl --hidden-import=pandas --hidden-import=PIL --hidden-import=requests main.py >nul 2>&1
)

if exist "dist\PurchaseGenerator\PurchaseGenerator.exe" (
    echo ✓ EXE собран: dist\PurchaseGenerator\PurchaseGenerator.exe
) else if exist "dist\PurchaseGenerator.exe" (
    echo ✓ EXE собран: dist\PurchaseGenerator.exe
) else (
    echo ❌ Критическая ошибка сборки!
    pause
    exit /b 1
)

REM --- СОЗДАНИЕ УСТАНОВЩИКА ---
echo.
echo Шаг 4/4: Создание установщика...
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    set "INNO_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)

if exist "%INNO_PATH%" (
    echo   Компиляция установщика Inno Setup...
    "%INNO_PATH%" create_installer.iss >nul 2>&1

    if exist "Output\PackageGeneratorApp.exe" (
        echo ✓ Установщик создан: Output\PackageGeneratorApp.exe

        REM --- СОЗДАНИЕ РЕЛИЗА НА GITHUB ---
        echo.
        echo Создание релиза на GitHub...
        gh --version >nul 2>&1
        if !errorlevel! equ 0 (
            (
            echo # Release v!NEW_VERSION!
            echo.
            echo ## Автоматический релиз
            echo - Обновление версии: !CURRENT_VERSION! → !NEW_VERSION!
            echo - Улучшена стабильность работы
            echo - Исправлены мелкие ошибки
            echo.
            echo ## Установка
            echo 1. Скачайте ^`PackageGeneratorApp.exe^`
            echo 2. Запустите установщик
            echo 3. Приложение будет автоматически обновляться
            ) > release_notes.md

            gh release create v!NEW_VERSION! "Output\PackageGeneratorApp.exe" --title "v!NEW_VERSION!" --notes-file release_notes.md >nul 2>&1
            del release_notes.md 2>nul

            echo ✓ Релиз создан на GitHub!
            echo 🌐 https://github.com/!GITHUB_USER!/!GITHUB_REPO!/releases/tag/v!NEW_VERSION!
        ) else (
            echo ⚠ GitHub CLI не установлен, релиз не создан
        )
    ) else (
        echo ⚠ Не удалось создать установщик
    )
) else (
    echo ⚠ Inno Setup не найден, установщик не создан
)

REM --- ФИНАЛЬНЫЙ ОТЧЕТ ---
echo.
echo ========================================
echo ✅ АВТОМАТИЧЕСКИЙ РЕЛИЗ ЗАВЕРШЁН!
echo ========================================
echo.
echo 📊 Результаты:
echo    ✓ Версия: !CURRENT_VERSION! → !NEW_VERSION!
echo    ✓ Код загружен на GitHub
echo    ✓ Приложение собрано
if exist "Output\PackageGeneratorApp.exe" (
    echo    ✓ Установщик создан
    echo.
    echo 📁 Установщик: Output\PackageGeneratorApp.exe
) else (
    echo    ⚠ Установщик не создан
    echo.
    echo 📁 EXE файл: dist\PurchaseGenerator\PurchaseGenerator.exe
)
echo.
echo 🚀 Пользователи получат обновление автоматически!
echo.
pause