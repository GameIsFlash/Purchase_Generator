; -- create_installer.iss --
; Скрипт для создания установщика PackageGeneratorApp

[Setup]
AppName=PackageGeneratorApp
AppVersion=1.0.5
AppPublisher=GameIsFlash
AppPublisherURL=https://github.com/GameIsFlash/Purchase_Generator
DefaultDirName={autopf}\PackageGeneratorApp
DefaultGroupName=PackageGeneratorApp
OutputDir=Output
OutputBaseFilename=PackageGeneratorApp
SetupIconFile=C:\Dev\Purchase_generator_final\icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern
VersionInfoVersion=1.0.5
VersionInfoCompany=GameIsFlash
VersionInfoDescription=Генератор покупок

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"

[Files]
; Копируем собранное приложение
Source: "C:\Dev\Purchase_generator_final\dist\PurchaseGenerator.exe"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
; Копируем папку data
Source: "C:\Dev\Purchase_generator_final\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Сборщик"; Filename: "{app}\PurchaseGenerator.exe"
Name: "{autodesktop}\Сборщик"; Filename: "{app}\PurchaseGenerator.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PurchaseGenerator.exe"; Description: "Запустить Сборщик"; Flags: nowait postinstall skipifsilent