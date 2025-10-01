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
set GITHUB_URL=https://github.com/GameIsFlash/Purchase_Generator.git
set VENV_PATH=C:\Dev\Purchase_generator_final\.venv

REM --- ПРОВЕРКА VIRTUAL ENVIRONMENT ---
echo Проверка виртуального окружения...
if exist "!VENV_PATH!\Scripts\activate.bat" (
    echo Активация виртуального окружения...
    call "!VENV_PATH!\Scripts\activate.bat"
    echo Виртуальное окружение активировано
) else (
    echo ВНИМАНИЕ: Виртуальное окружение не найдено по пути: !VENV_PATH!
    echo Убедись что PyInstaller установлен в системе
)

REM --- ПРОВЕРКА GIT РЕПОЗИТОРИЯ ---
echo Проверка Git репозитория...
git status >nul 2>&1
if !errorlevel! neq 0 (
    echo ОШИБКА: Это не Git репозиторий!
    echo Инициализируем Git...
    git init
    git add .
    git commit -m "Initial commit"
)

REM --- ПРОВЕРКА REMOTE ORIGIN ---
echo Проверка remote origin...
git remote get-url origin >nul 2>&1
if !errorlevel! neq 0 (
    echo Remote origin не настроен.
    echo Добавляем origin: !GITHUB_URL!
    git remote add origin "!GITHUB_URL!"
)

REM --- СОЗДАЕМ ВРЕМЕННЫЕ PYTHON СКРИПТЫ ДЛЯ ЧТЕНИЯ ВЕРСИИ ---
echo import re > get_version.py
echo content = open('main.py', 'r', encoding='utf-8').read() >> get_version.py
echo match = re.search(r'CURRENT_VERSION\s*=\s*["'']([0-9.]+)["'']', content) >> get_version.py
echo if match: >> get_version.py
echo     print(match.group(1)) >> get_version.py
echo else: >> get_version.py
echo     print('0.0.0') >> get_version.py

REM --- ПОЛУЧЕНИЕ ТЕКУЩЕЙ ВЕРСИИ ---
echo Получение текущей версии...
python get_version.py > temp_version.txt
set /p CURRENT_VERSION=<temp_version.txt
del get_version.py
del temp_version.txt

if "!CURRENT_VERSION!"=="0.0.0" (
    echo Не удалось найти CURRENT_VERSION в main.py
    echo Создаем первую версию 1.0.0
    set CURRENT_VERSION=1.0.0
    set NEW_VERSION=1.0.0
    set FIRST_RELEASE=1
) else (
    echo Текущая версия: !CURRENT_VERSION!
    echo.

    REM --- РАЗБИЕНИЕ ВЕРСИИ НА ЧАСТИ ---
    for /f "tokens=1,2,3 delims=." %%a in ("!CURRENT_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
        set PATCH=%%c
    )

    REM --- ЗАПРОС НОВОЙ ВЕРСИИ ---
    set /p VERSION_TYPE="Выбери тип обновления (1 - patch, 2 - minor, 3 - major): "

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
)

echo.
echo 🚀 Начинаем процесс релиза v!NEW_VERSION!...
echo.

REM --- СОЗДАЕМ СКРИПТ ДЛЯ ОБНОВЛЕНИЯ main.py ---
echo import re > update_main.py
echo content = open('main.py', 'r', encoding='utf-8').read() >> update_main.py
echo new_version = "!NEW_VERSION!" >> update_main.py
echo new_content = re.sub(r'CURRENT_VERSION\s*=\s*["'']([0-9.]+)["'']', 'CURRENT_VERSION = "' + new_version + '"', content) >> update_main.py
echo open('main.py', 'w', encoding='utf-8').write(new_content) >> update_main.py

REM --- СОЗДАЕМ СКРИПТ ДЛЯ ОБНОВЛЕНИЯ create_installer.iss ---
echo import re > update_iss.py
echo content = open('create_installer.iss', 'r', encoding='utf-8').read() >> update_iss.py
echo new_version = "!NEW_VERSION!" >> update_iss.py
echo content = re.sub(r'AppVersion=[0-9.]+', 'AppVersion=' + new_version, content) >> update_iss.py
echo content = re.sub(r'VersionInfoVersion=[0-9.]+', 'VersionInfoVersion=' + new_version, content) >> update_iss.py
echo open('create_installer.iss', 'w', encoding='utf-8').write(content) >> update_iss.py

REM --- ОБНОВЛЕНИЕ ВЕРСИИ В ФАЙЛАХ ---
echo Шаг 1: Обновление версии в файлах...

echo Обновление main.py...
python update_main.py
if !errorlevel! neq 0 (
    echo Ошибка при обновлении main.py
    pause
    exit /b 1
)

echo Обновление create_installer.iss...
python update_iss.py
if !errorlevel! neq 0 (
    echo Ошибка при обновлении create_installer.iss
    pause
    exit /b 1
)

del update_main.py
del update_iss.py

REM --- ЧТЕНИЕ ОПИСАНИЯ ОБНОВЛЕНИЯ ---
echo Шаг 2: Чтение описания обновления...

if exist "update_description.txt" (
    echo Найден файл update_description.txt
    copy update_description.txt changelog_temp.txt >nul
) else (
    echo Файл update_description.txt не найден, создаем стандартное описание
    echo. > changelog_temp.txt
)

REM --- КОММИТ И ПУШ НА GITHUB ---
echo Шаг 3: Коммит и пуш на GitHub...

git add .
git commit -m "🚀 Release v!NEW_VERSION!"

echo Пуш в репозиторий...
git push -u origin master

if !errorlevel! neq 0 (
    echo ОШИБКА: Не удалось запушить в GitHub
    echo Продолжаем сборку без пуша на GitHub...
    set GIT_ERROR=1
)

REM --- СБОРКА ПРИЛОЖЕНИЯ ---
echo Шаг 4: Сборка приложения...

echo Очистка предыдущих сборок...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo Проверка PyInstaller...
pyinstaller --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ОШИБКА: PyInstaller не найден!
    echo.
    echo Установи PyInstaller: pip install pyinstaller
    echo Или активируй виртуальное окружение вручную
    echo.
    pause
    exit /b 1
)

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

REM --- ПОДПИСЫВАНИЕ ФАЙЛОВ ---
echo Шаг 5: Подписывание файлов...

set SIGNTOOL_PATH=C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe
if exist "!SIGNTOOL_PATH!" (
    echo Подписывание EXE...
    "!SIGNTOOL_PATH!" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /v "dist\PurchaseGenerator\PurchaseGenerator.exe"

    echo Подписывание установщика...
    "!SIGNTOOL_PATH!" sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /v "Output\PackageGeneratorApp_Setup.exe"
) else (
    echo Windows SDK не найден. Пропускаем подписывание.
)

REM --- СОЗДАНИЕ РЕЛИЗА НА GITHUB ---
echo Шаг 6: Создание релиза на GitHub...

if defined GIT_ERROR (
    echo Пропускаем создание релиза из-за ошибок Git
) else (
    echo Создание описания релиза...
    echo # Release v!NEW_VERSION! > changelog.md
    echo. >> changelog.md
    echo ## Что нового в этой версии: >> changelog.md
    echo. >> changelog.md

    REM --- ДОБАВЛЯЕМ ОПИСАНИЕ ИЗ ФАЙЛА ИЛИ СТАНДАРТНОЕ ---
    if exist "changelog_temp.txt" (
        type changelog_temp.txt >> changelog.md
        del changelog_temp.txt
    ) else (
        if defined FIRST_RELEASE (
            echo - Первый релиз приложения >> changelog.md
            echo - Все основные функции работают >> changelog.md
        ) else (
            echo - Автоматическое обновление >> changelog.md
            echo - Исправление ошибок >> changelog.md
            echo - Улучшение производительности >> changelog.md
        )
    )

    echo. >> changelog.md
    echo ## Установка: >> changelog.md
    echo 1. Скачайте ^`PackageGeneratorApp_Setup.exe^` >> changelog.md
    echo 2. Запустите установщик >> changelog.md
    echo 3. Приложение автоматически обновляется >> changelog.md

    REM --- УДАЛЯЕМ ФАЙЛ ОПИСАНИЯ ПОСЛЕ ИСПОЛЬЗОВАНИЯ ---
    if exist "update_description.txt" (
        echo Удаление update_description.txt после использования...
        del update_description.txt
    )

    gh release create v!NEW_VERSION! "Output\PackageGeneratorApp_Setup.exe" --title "v!NEW_VERSION!" --notes-file changelog.md

    if !errorlevel! neq 0 (
        echo Ошибка при создании релиза
        echo Убедись, что:
        echo 1. Установлен GitHub CLI: winget install GitHub.cli
        echo 2. Выполнен вход: gh auth login
        echo 3. Токен имеет права на создание релизов
    )

    REM --- ОЧИСТКА ---
    del changelog.md 2>nul
)

echo.
echo ========================================
echo ✅ РЕЛИЗ v!NEW_VERSION! УСПЕШНО ЗАВЕРШЕН!
echo ========================================
echo.
if defined FIRST_RELEASE (
    echo 🎉 СОЗДАН ПЕРВЫЙ РЕЛИЗ!
) else (
    echo Что было сделано:
    echo ✓ Версия обновлена с !CURRENT_VERSION! до !NEW_VERSION!
)
echo ✓ EXE файл собран
echo ✓ Установщик создан
echo ✓ Файлы подписаны
if defined GIT_ERROR (
    echo ⚠ Код НЕ запушен на GitHub (ошибка Git)
    echo ⚠ Релиз НЕ создан на GitHub
) else (
    echo ✓ Код запушен на GitHub
    echo ✓ Релиз создан на GitHub
    echo.
    echo Ссылка на релиз: https://github.com/!GITHUB_USER!/!GITHUB_REPO!/releases/tag/v!NEW_VERSION!
)
echo.

pause