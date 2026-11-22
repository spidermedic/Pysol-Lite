; Inno Setup script for PySol Lite (Windows installer).
; Build with scripts\build_windows.ps1 (it passes /DAppVersion=<YY.MM>), after
; PyInstaller has produced dist\PySol Lite.
#ifndef AppVersion
  #define AppVersion "0.0"
#endif

[Setup]
AppId={{6F1D2C54-3B7A-4E0B-9A55-8C2D7E41B3A9}
AppName=PySol Lite
AppVersion={#AppVersion}
AppPublisher=Doug Martin
AppPublisherURL=https://github.com/spidermedic/Pysol-Lite
DefaultDirName={autopf}\PySol Lite
DefaultGroupName=PySol Lite
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.md
SetupIconFile=..\data\pysol.ico
UninstallDisplayIcon={app}\PySol Lite.exe
OutputDir=..\dist
OutputBaseFilename=PySol-Lite-{#AppVersion}-Windows-setup
Compression=lzma2
SolidCompression=yes
; per-user install by default; the user can choose all users in the dialog
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\PySol Lite\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\PySol Lite"; Filename: "{app}\PySol Lite.exe"
Name: "{group}\Uninstall PySol Lite"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PySol Lite"; Filename: "{app}\PySol Lite.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PySol Lite.exe"; Description: "Launch PySol Lite"; Flags: nowait postinstall skipifsilent
