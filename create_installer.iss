; -- create_installer.iss --
; Скрипт для создания установщика PackageGeneratorApp

[Setup]
AppName=PackageGeneratorApp
AppVersion=1.0.14
AppPublisher=GameIsFlash
AppPublisherURL=https://github.com/GameIsFlash/Purchase_Generator
DefaultDirName={autopf}\PackageGeneratorApp
DefaultGroupName=PackageGeneratorApp
OutputDir=Output
OutputBaseFilename=PackageGeneratorApp
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern
VersionInfoVersion=1.0.14
VersionInfoCompany=GameIsFlash
VersionInfoDescription=Генератор покупок
AllowNoIcons=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"

[Files]
Source: "dist\PurchaseGenerator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "dist\PurchaseGenerator.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PackageGeneratorApp"; Filename: "{app}\PurchaseGenerator.exe"
Name: "{autodesktop}\PackageGeneratorApp"; Filename: "{app}\PurchaseGenerator.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PurchaseGenerator.exe"; Description: "Запустить приложение"; Flags: nowait postinstall skipifsilent