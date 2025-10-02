@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo    АВТОМАТИЧЕСКИЙ РЕЛИЗ PACKAGEGENERATOR
echo ========================================
echo.

REM --- КОНФИГУРАЦИЯ ---
set REPO_PATH=%~dp0
set GITHUB_USER=GameIsFlash
set GITHUB_REPO=Purchase_Generator

REM --- ПЕРЕХОД В ПАПКУ ПРОЕКТА ---
cd /d "%REPO_PATH%"

REM --- ЗАЩИТА SPEC ФАЙЛА ---
if not exist "PurchaseGenerator.spec" (
    echo ОШИБКА: PurchaseGenerator.spec не найден!
    echo Создайте файл спецификации PyInstaller
    pause
    exit /b 1
)

REM --- ПОЛУЧЕНИЕ ВЕРСИИ ---
for /f "tokens=2 delims=^=" %%i in ('findstr "CURRENT_VERSION" main.py') do (
    set VERSION_LINE=%%i
)
set CURRENT_VERSION=!VERSION_LINE:"=!
set CURRENT_VERSION=!CURRENT_VERSION: =!
echo Текущая версия: !CURRENT_VERSION!

REM --- ЗАПРОС НОВОЙ ВЕРСИИ ---
echo.
echo Введите новую версию (текущая: !CURRENT_VERSION!):
set /p NEW_VERSION=Новая версия:

if "!NEW_VERSION!"=="" (
    echo Версия не введена!
    pause
    exit /b 1
)

REM --- ОБНОВЛЕНИЕ ВЕРСИИ ---
echo.
echo Обновление версии в файлах...
python -c "content = open('main.py', 'r', encoding='utf-8').read(); new_content = content.replace('CURRENT_VERSION = \"!CURRENT_VERSION!\"', 'CURRENT_VERSION = \"!NEW_VERSION!\"'); open('main.py', 'w', encoding='utf-8').write(new_content)"
python -c "content = open('create_installer.iss', 'r', encoding='utf-8').read(); import re; content = re.sub(r'AppVersion=[0-9.]+', 'AppVersion=!NEW_VERSION!', content); content = re.sub(r'VersionInfoVersion=[0-9.]+', 'VersionInfoVersion=!NEW_VERSION!', content); open('create_installer.iss', 'w', encoding='utf-8').write(content)"

REM --- КОММИТ ИЗМЕНЕНИЙ ---
echo.
echo Коммит изменений...
git add .
git commit -m "🚀 Release v!NEW_VERSION!"
git push

REM --- СБОРКА ПРИЛОЖЕНИЯ ---
echo.
echo Сборка приложения...
echo Очистка предыдущих сборок...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo Запуск PyInstaller...
pyinstaller PurchaseGenerator.spec --clean

if not exist "dist\PurchaseGenerator.exe" (
    echo ОШИБКА: Сборка не удалась!
    pause
    exit /b 1
)

echo ✓ Приложение собрано!

REM --- СОЗДАНИЕ УСТАНОВЩИКА ---
echo.
echo Создание установщика...
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% (
    echo ОШИБКА: Inno Setup не найден!
    pause
    exit /b 1
)

%INNO_PATH% create_installer.iss

if not exist "Output\PackageGeneratorApp.exe" (
    echo ОШИБКА: Установщик не создан!
    pause
    exit /b 1
)

echo ✓ Установщик создан!

REM --- СОЗДАНИЕ РЕЛИЗА ---
echo.
echo Создание релиза на GitHub...
gh release create v!NEW_VERSION! "Output\PackageGeneratorApp.exe" --title "v!NEW_VERSION!" --notes "Автоматический релиз v!NEW_VERSION!"

if !errorlevel! equ 0 (
    echo ✓ Релиз создан на GitHub!
    echo.
    echo Ссылка: https://github.com/!GITHUB_USER!/!GITHUB_REPO!/releases/tag/v!NEW_VERSION!
) else (
    echo ⚠ Не удалось создать релиз через GitHub CLI
    echo Создайте релиз вручную: https://github.com/!GITHUB_USER!/!GITHUB_REPO!/releases
)

echo.
echo ========================================
echo ✅ РЕЛИЗ v!NEW_VERSION! ЗАВЕРШЁН!
echo ========================================
echo.
pause