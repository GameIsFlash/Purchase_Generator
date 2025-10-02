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

REM --- ПРОВЕРКА VIRTUAL ENVIRONMENT ---
echo.
echo Проверка виртуального окружения...
if exist "%VENV_PATH%\Scripts\activate.bat" (
    echo Активация виртуального окружения...
    call "%VENV_PATH%\Scripts\activate.bat"
    echo ✓ Виртуальное окружение активировано
) else (
    echo ⚠ Виртуальное окружение не найдено, используем системный Python
    python --version
)

REM --- ПРОВЕРКА PYINSTALLER ---
echo.
echo Проверка PyInstaller...
pyinstaller --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ ОШИБКА: PyInstaller не найден!
    echo Установите: pip install pyinstaller
    pause
    exit /b 1
)
echo ✓ PyInstaller доступен

REM --- ЗАЩИТА SPEC ФАЙЛА ---
if not exist "PurchaseGenerator.spec" (
    echo ❌ ОШИБКА: PurchaseGenerator.spec не найден!
    echo Создайте файл спецификации PyInstaller
    pause
    exit /b 1
)

REM --- ПОЛУЧЕНИЕ ВЕРСИИ ---
for /f "tokens=2 delims=^=" %%i in ('findstr "CURRENT_VERSION" main.py') do (
    set VERSION_LINE=%%i
)
set "CURRENT_VERSION=!VERSION_LINE:"=!"
set "CURRENT_VERSION=!CURRENT_VERSION: =!"
echo Текущая версия: !CURRENT_VERSION!

REM --- ЗАПРОС НОВОЙ ВЕРСИИ ---
echo.
echo Введите новую версию (текущая: !CURRENT_VERSION!):
set /p NEW_VERSION=Новая версия:

if "!NEW_VERSION!"=="" (
    echo ❌ Версия не введена!
    pause
    exit /b 1
)

REM --- ПОДТВЕРЖДЕНИЕ ---
echo.
echo Подтвердите обновление:
echo Старая версия: !CURRENT_VERSION!
echo Новая версия:  !NEW_VERSION!
set /p CONFIRM=Продолжить? (y/n):
if /i not "!CONFIRM!"=="y" (
    echo Отменено пользователем
    pause
    exit /b 1
)

REM --- ОБНОВЛЕНИЕ ВЕРСИИ ---
echo.
echo Шаг 1/5: Обновление версии в файлах...

echo   Обновление main.py...
python -c "content = open('main.py', 'r', encoding='utf-8').read(); new_content = content.replace('CURRENT_VERSION = \"!CURRENT_VERSION!\"', 'CURRENT_VERSION = \"!NEW_VERSION!\"'); open('main.py', 'w', encoding='utf-8').write(new_content)"

echo   Обновление create_installer.iss...
python -c "content = open('create_installer.iss', 'r', encoding='utf-8').read(); import re; content = re.sub(r'AppVersion=[0-9.]+', 'AppVersion=!NEW_VERSION!', content); content = re.sub(r'VersionInfoVersion=[0-9.]+', 'VersionInfoVersion=!NEW_VERSION!', content); open('create_installer.iss', 'w', encoding='utf-8').write(content)"

echo ✓ Версии обновлены

REM --- КОММИТ ИЗМЕНЕНИЙ ---
echo.
echo Шаг 2/5: Коммит изменений в Git...

git add .
git commit -m "🚀 Release v!NEW_VERSION!"
git push

if !errorlevel! equ 0 (
    echo ✓ Изменения запушены на GitHub
) else (
    echo ⚠ Ошибка при пуше в GitHub, продолжаем...
)

REM --- СБОРКА ПРИЛОЖЕНИЯ ---
echo.
echo Шаг 3/5: Сборка приложения...

echo   Очистка предыдущих сборок...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

echo   Запуск PyInstaller...
pyinstaller PurchaseGenerator.spec --clean

if !errorlevel! neq 0 (
    echo ❌ ОШИБКА: Сборка PyInstaller не удалась!
    pause
    exit /b 1
)

if not exist "dist\PurchaseGenerator.exe" (
    echo ❌ ОШИБКА: EXE файл не создан!
    dir dist 2>nul || echo Папка dist не существует
    pause
    exit /b 1
)

echo ✓ Приложение собрано: dist\PurchaseGenerator.exe

REM --- СОЗДАНИЕ УСТАНОВЩИКА ---
echo.
echo Шаг 4/5: Создание установщика...

set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    echo ❌ ОШИБКА: Inno Setup не найден!
    echo Установите Inno Setup: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo   Компиляция установщика...
"%INNO_PATH%" create_installer.iss

if !errorlevel! neq 0 (
    echo ❌ ОШИБКА: Создание установщика не удалось!
    pause
    exit /b 1
)

if not exist "Output\PackageGeneratorApp.exe" (
    echo ❌ ОШИБКА: Установщик не создан!
    dir Output 2>nul || echo Папка Output не существует
    pause
    exit /b 1
)

echo ✓ Установщик создан: Output\PackageGeneratorApp.exe

REM --- СОЗДАНИЕ РЕЛИЗА ---
echo.
echo Шаг 5/5: Создание релиза на GitHub...

echo   Проверка GitHub CLI...
gh --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ⚠ GitHub CLI не установлен, пропускаем создание релиза
    goto SKIP_RELEASE
)

echo   Создание описания релиза...
(
echo # Release v!NEW_VERSION!
echo.
echo ## Что нового
echo - Автоматическое обновление
echo - Исправления и улучшения
echo.
echo ## Установка
echo 1. Скачайте `PackageGeneratorApp.exe`
echo 2. Запустите установщик
echo 3. Приложение будет автоматически обновляться
) > release_notes.md

echo   Создание релиза...
gh release create v!NEW_VERSION! "Output\PackageGeneratorApp.exe" --title "v!NEW_VERSION!" --notes-file release_notes.md

if !errorlevel! equ 0 (
    echo ✓ Релиз создан на GitHub!
    echo.
    echo 🌐 Ссылка: https://github.com/!GITHUB_USER!/!GITHUB_REPO!/releases/tag/v!NEW_VERSION!
) else (
    echo ⚠ Не удалось создать релиз через GitHub CLI
)

del release_notes.md 2>nul

:SKIP_RELEASE

REM --- ЗАВЕРШЕНИЕ ---
echo.
echo ========================================
echo ✅ РЕЛИЗ v!NEW_VERSION! ЗАВЕРШЁН!
echo ========================================
echo.
echo 📁 Файлы:
echo    • dist\PurchaseGenerator.exe
echo    • Output\PackageGeneratorApp.exe
echo.
echo 📋 Действия:
echo    • Версия обновлена: !CURRENT_VERSION! → !NEW_VERSION!
echo    • Код загружен на GitHub
echo    • Приложение собрано
echo    • Установщик создан
echo.
pause