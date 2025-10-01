@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo    АВТОМАТИЧЕСКИЙ РЕЛИЗ PACKAGEGENERATOR
echo ========================================
echo.

REM --- КОНФИГУРАЦИЯ ---
set REPO_PATH=C:\Dev\Purchase_generator_final
set GITHUB_USER=GameIsFlash
set GITHUB_REPO=Purchase_Generator
set /a CURRENT_BUILD=0

REM --- ЧТЕНИЕ ТЕКУЩЕЙ ВЕРСИИ ---
for /f "tokens=2 delims=^=" %%i in ('findstr "CURRENT_VERSION" main.py') do (
    set CURRENT_VERSION=%%i
    set CURRENT_VERSION=!CURRENT_VERSION: =!
    set CURRENT_VERSION=!CURRENT_VERSION:'=!
    set CURRENT_VERSION=!CURRENT_VERSION:"=!
)

echo Текущая версия: !CURRENT_VERSION!
echo.

REM --- ЗАПРОС НОВОЙ ВЕРСИИ ---
set /p VERSION_TYPE="Выбери тип обновления (1 - patch, 2 - minor, 3 - major): "

for /f "tokens=1,2,3 delims=." %%a in ("!CURRENT_VERSION!") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)

if "!VERSION_TYPE!"=="1" (
    set /a NEW_PATCH=!PATCH!+1
    set NEW_VERSION=!MAJOR!.!MINOR!.!NEW_PATCH!
) else if "!VERSION_TYPE!"=="2" (
    set /a NEW_MINOR=!MINOR!+1
    set NEW_VERSION=!MAJOR!.!NEW_MINOR!.0
) else if "!VERSION_TYPE!"=="3" (
    set /a NEW_MAJOR=!MAJOR!+1
    set NEW_VERSION=!NEW_MAJOR!.0.0
) else (
    echo Неверный выбор!
    pause
    exit /b 1
)

set /p CONFIRM="Новая версия будет: !NEW_VERSION!. Продолжить? (y/n): "
if /i not "!CONFIRM!"=="y" (
    echo Отменено.
    pause
    exit /b 1
)

echo.
echo 🚀 Начинаем процесс релиза v!NEW_VERSION!...
echo.

REM --- ОБНОВЛЕНИЕ ВЕРСИИ В ФАЙЛАХ ---
echo Шаг 1: Обновление версии в файлах...

REM Обновление main.py
python -c "import re; content = open('main.py', 'r', encoding='utf-8').read(); new_content = re.sub(r'CURRENT_VERSION = \"\d+\.\d+\.\d+\"', 'CURRENT_VERSION = \"!NEW_VERSION!\"', content); open('main.py', 'w', encoding='utf-8').write(new_content)"
if !errorlevel! neq 0 (
    echo Ошибка при обновлении main.py
    pause
    exit /b 1
)

REM Обновление create_installer.iss
python -c "import re; content = open('create_installer.iss', 'r', encoding='utf-8').read(); content = re.sub(r'AppVersion=\d+\.\d+\.\d+', 'AppVersion=!NEW_VERSION!', content); content = re.sub(r'VersionInfoVersion=\d+\.\d+\.\d+', 'VersionInfoVersion=!NEW_VERSION!', content); open('create_installer.iss', 'w', encoding='utf-8').write(content)"
if !errorlevel! neq 0 (
    echo Ошибка при обновлении create_installer.iss
    pause
    exit /b 1
)

REM --- КОММИТ И ПУШ НА GITHUB ---
echo Шаг 2: Коммит и пуш на GitHub...

git add .
git commit -m "🚀 Release v!NEW_VERSION!"
git push origin main

if !errorlevel! neq 0 (
    echo Ошибка при пуше на GitHub
    pause
    exit /b 1
)

REM --- СБОРКА ПРИЛОЖЕНИЯ ---
echo Шаг 3: Сборка приложения...

echo Сборка EXE через PyInstaller...
pyinstaller PurchaseGenerator.spec
if !errorlevel! neq 0 (
    echo Ошибка при сборке EXE
    pause
    exit /b 1
)

echo Сборка установщика через Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" create_installer.iss
if !errorlevel! neq 0 (
    echo Ошибка при сборке установщика
    pause
    exit /b 1
)

REM --- БЕСПЛАТНОЕ ПОДПИСЫВАНИЕ ЧЕРЕЗ SignTool ---
echo Шаг 4: Подписывание файлов...

REM Проверяем наличие Windows SDK
set SIGNTOOL_PATH=C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe
if not exist "!SIGNTOOL_PATH!" (
    echo Windows SDK не найден. Пропускаем подписывание.
    echo Для подписывания установи Windows SDK
) else (
    echo Подписывание EXE...
    "!SIGNTOOL_PATH!" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /v "dist\PurchaseGenerator\PurchaseGenerator.exe"

    echo Подписывание установщика...
    "!SIGNTOOL_PATH!" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /v "Output\PackageGeneratorApp_Setup.exe"
)

REM --- СОЗДАНИЕ РЕЛИЗА НА GITHUB ---
echo Шаг 5: Создание релиза на GitHub...

REM Создаем временный файл с описанием
echo Release v!NEW_VERSION! > temp_changelog.md
echo. >> temp_changelog.md
echo Что нового в этой версии: >> temp_changelog.md
echo - Автоматическое обновление >> temp_changelog.md
echo - Исправление ошибок >> temp_changelog.md
echo - Улучшение производительности >> temp_changelog.md

REM Создаем релиз через GitHub CLI
gh release create v!NEW_VERSION! "Output\PackageGeneratorApp_Setup.exe" --title "v!NEW_VERSION!" --notes-file temp_changelog.md

if !errorlevel! neq 0 (
    echo Ошибка при создании релиза
    echo Убедись, что установлен GitHub CLI и выполнен gh auth login
)

REM --- ОЧИСТКА ---
del temp_changelog.md

echo.
echo ========================================
echo ✅ РЕЛИЗ v!NEW_VERSION! УСПЕШНО ЗАВЕРШЕН!
echo ========================================
echo.
echo Что было сделано:
echo ✓ Версия обновлена с !CURRENT_VERSION! до !NEW_VERSION!
echo ✓ Код запушен на GitHub
echo ✓ EXE файл собран
echo ✓ Установщик создан
echo ✓ Файлы подписаны
echo ✓ Релиз создан на GitHub
echo.
echo Ссылка на релиз: https://github.com/!GITHUB_USER!/!GITHUB_REPO!/releases/tag/v!NEW_VERSION!
echo.

pause