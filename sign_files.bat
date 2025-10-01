@echo off
echo Подписание файлов...

set SIGNPATH_API_TOKEN=ТВОЙ_API_ТОКЕН
set PROJECT_SLUG=package-generator-app
set SIGNING_POLICY_SLUG=open-source

echo Подписание основного EXE...
"c:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe" sign /fd SHA256 /tr http://timestamp.sectigo.com /td SHA256 "dist\PurchaseGenerator\PurchaseGenerator.exe"

echo Подписание установщика...
"c:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe" sign /fd SHA256 /tr http://timestamp.sectigo.com /td SHA256 "Output\PackageGeneratorApp.exe"

echo Готово!
pause