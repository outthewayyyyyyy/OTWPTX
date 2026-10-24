; Windows installer. CI passes the version: ISCC /DMyAppVersion=1.0.0 installer.iss
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
AppId={{6C1F5E0B-7A8E-4C55-9F2B-0D7B4E9A1C11}
AppName=OTW PTX
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\OTW PTX
DefaultGroupName=OTW PTX
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputBaseFilename=OTW-PTX-{#MyAppVersion}-windows-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\OTW PTX.exe

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"

[Files]
Source: "dist\OTW PTX\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\OTW PTX"; Filename: "{app}\OTW PTX.exe"
Name: "{autodesktop}\OTW PTX"; Filename: "{app}\OTW PTX.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OTW PTX.exe"; Description: "Open OTW PTX now"; Flags: nowait postinstall skipifsilent
