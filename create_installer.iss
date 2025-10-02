; -- create_installer.iss --
; Скрипт для создания установщика PackageGeneratorApp

[Setup]
AppName=PackageGeneratorApp
AppVersion=1.0.13
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
VersionInfoVersion=1.0.13
VersionInfoCompany=GameIsFlash
VersionInfoDescription=Генератор покупок
AllowNoIcons=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"

[Files]
Source: "dist\PurchaseGenerator.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PackageGeneratorApp"; Filename: "{app}\PurchaseGenerator.exe"
Name: "{autodesktop}\PackageGeneratorApp"; Filename: "{app}\PurchaseGenerator.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PurchaseGenerator.exe"; Description: "Запустить приложение"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /f /im PurchaseGenerator.exe"; Flags: runhidden

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;