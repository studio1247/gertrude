#define GertrudeVersion GetFileVersion("dist/gertrude.exe")

[Setup]
AppName=Gertrude
AppVerName=Gertrude {#GertrudeVersion}
AppVersion={#GertrudeVersion}
AppPublisher=Bertrand Songis
AppPublisherURL=http://www.gertrude-logiciel.org
AppSupportURL=http://www.gertrude-logiciel.org
AppUpdatesURL=http://www.gertrude-logiciel.org
VersionInfoVersion={#GertrudeVersion}
VersionInfoCompany=Bertrand Songis
VersionInfoProductName=Gertrude
AppCopyright=Copyright © 2005-2014 - Bertrand Songis

DefaultDirName={pf}\Gertrude
DefaultGroupName=Gertrude

OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes

WizardImageBackColor=clWhite
SetupIconFile=bitmaps_dist\gertrude.ico
WizardImageFile=bitmaps_dist\setup_gertrude.bmp
WizardSmallImageFile=bitmaps_dist\setup_gertrude_mini.bmp
UninstallDisplayIcon={app}\gertrude.exe

[Messages]
BeveledLabel=Gertrude

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[InstallDelete]
Type: files; Name: "{app}\*.py"
Type: files; Name: "{app}\demo.db"
Type: files; Name: "{app}\*.php"
Type: files; Name: "{app}\*.pyc"
Type: files; Name: "{app}\*.log"

[Dirs]
Name: "{app}"; Permissions:users-modify   

[Files]
; ---> Gertrude directory
Source: "dist\gertrude\*.exe";                   DestDir: "{app}";                     Flags: ignoreversion
Source: "dist\gertrude\*.ini.dist";              DestDir: "{app}";                     Flags: ignoreversion
Source: "dist\gertrude\demo.db";                 DestDir: "{app}";                     Flags: ignoreversion
Source: "dist\gertrude\*.php";                   DestDir: "{app}";                     Flags: ignoreversion
Source: "dist\gertrude\*.dll";                   DestDir: "{app}";                     Flags: ignoreversion
Source: "dist\gertrude\*.pyd";                   DestDir: "{app}";                     Flags: ignoreversion
;Source: "dist\gertrude\Microsoft.VC90.CRT\*.*";  DestDir: "{app}\Microsoft.VC90.CRT";  Flags: ignoreversion
;Source: "dist\gertrude\Microsoft.VC90.MFC\*.*";  DestDir: "{app}\Microsoft.VC90.CRT";  Flags: ignoreversion

; ---> Subdirectories
Source: "dist\gertrude\bitmaps_dist\*";          DestDir: "{app}\bitmaps_dist";        Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\gertrude\bitmaps_dist\pictos\*";   DestDir: "{app}\bitmaps_dist\pictos"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\gertrude\templates_dist\*";        DestDir: "{app}\templates_dist";      Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Gertrude";       Filename: "{app}\gertrude.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Gertrude"; Filename: "{app}\gertrude.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\gertrude.exe"; Description: "{cm:LaunchProgram,Gertrude}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; uninstallation removes the compiled python files
Type: files; Name: "{app}\*.pyc"









