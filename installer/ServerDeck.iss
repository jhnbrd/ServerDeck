; ServerDeck Windows installer (Inno Setup 6)
; Build the executable first:  .\scripts\build_release.ps1 -SkipInstaller

#define AppVersion "1.0.0"

[Setup]
AppId={{A4B8C2D1-7E3F-4A91-9B2C-1D5E6F708192}
AppName=ServerDeck
AppVersion={#AppVersion}
AppVerName=ServerDeck {#AppVersion}
AppPublisher=ServerDeck
AppSupportURL=https://github.com/jhnbrd/ServerDeck
AppUpdatesURL=https://github.com/jhnbrd/ServerDeck/releases
DefaultDirName={autopf}\ServerDeck
DefaultGroupName=ServerDeck
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
#ifnexist "..\dist\ServerDeck\ServerDeck.exe"
  #error "Build the executable first: .\scripts\build_release.ps1 -SkipInstaller"
#endif
OutputDir=output
OutputBaseFilename=ServerDeck-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\ServerDeck.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startup"; Description: "Start ServerDeck when &Windows starts"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\ServerDeck\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ServerDeck"; Filename: "{app}\ServerDeck.exe"; Comment: "Home Server Control Panel"
Name: "{autodesktop}\ServerDeck"; Filename: "{app}\ServerDeck.exe"; Tasks: desktopicon; Comment: "Home Server Control Panel"
Name: "{userstartup}\ServerDeck"; Filename: "{app}\ServerDeck.exe"; Tasks: startup; Comment: "Launch ServerDeck on login"

[Run]
Filename: "{app}\ServerDeck.exe"; Description: "Launch ServerDeck"; Flags: nowait postinstall skipifsilent
