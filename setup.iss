#define GertrudeVersion GetFileVersion("dist/gertrude.exe")

[Setup]
AppName=Gertrude
AppVerName=Gertrude {#GertrudeVersion}
AppVersion={#GertrudeVersion}
AppPublisher=Bertrand Songis
AppPublisherURL=http://gertrude.creches.free.fr
AppSupportURL=http://gertrude.creches.free.fr
AppUpdatesURL=http://gertrude.creches.free.fr
VersionInfoVersion={#GertrudeVersion}
VersionInfoCompany=Bertrand Songis
VersionInfoProductName=Gertrude
AppCopyright=Copyright © 2005-2009 - Bertrand Songis

DefaultDirName={pf}\Gertrude
DefaultGroupName=Gertrude

OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes

WizardImageBackColor=clWhite
SetupIconFile=bitmaps\setup_gertrude.ico
WizardImageFile=bitmaps\setup_gertrude.bmp
WizardSmallImageFile=bitmaps\setup_gertrude_mini.bmp
UninstallDisplayIcon={app}\gertrude.exe

[Messages]
BeveledLabel=Gertrude - v{#GertrudeVersion}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[InstallDelete]
Type: files; Name: "{app}\*.py"
Type: files; Name: "{app}\*.pyc"
Type: files; Name: "{app}\*.log"

[Files]
; ---> Gertrude directory
Source: "dist\*.py";                  DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\*.pyd";                 DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\*.exe";                 DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\*.dist";                DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\*.zip";                 DestDir: "{app}";                 Flags: ignoreversion
;      separate dll's, in order to not copy the POWRPROF.DLL
Source: "dist\python26.dll";          DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\pythoncom26.dll";       DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\pywintypes26.dll";      DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\sqlite3.dll";           DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\wxbase28uh_net_vc.dll"; DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\wxbase28uh_vc.dll";     DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\wxmsw28uh_adv_vc.dll";  DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\wxmsw28uh_core_vc.dll"; DestDir: "{app}";                 Flags: ignoreversion
Source: "dist\wxmsw28uh_html_vc.dll"; DestDir: "{app}";                 Flags: ignoreversion

; ---> Subdirectories
Source: "dist\bitmaps\*";             DestDir: "{app}\bitmaps";         Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\doc\*";                 DestDir: "{app}\doc";             Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\templates_dist\*";      DestDir: "{app}\templates_dist";  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Gertrude";       Filename: "{app}\gertrude.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Gertrude"; Filename: "{app}\gertrude.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\gertrude.exe"; Description: "{cm:LaunchProgram,Gertrude}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; uninstallation removes the compiled python files
Type: files; Name: "{app}\*.pyc"









