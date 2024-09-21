; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!
; https://www.kymoto.org/products/inno-script-studio/
; Some editing was required to handle the import of files in
; in designated folders. (It was necessary to append the folder
; name after {app} in the Source: statement prior to Flags.)
; Of course you should also have Inno Setup Downloads also installed from
; http://www.jrsoftware.org/isdl.php
;
; Seymour Shlien

#define MyAppName "EasyABC"
#define MyAppVersion "1.3.8.7"
#define MyAppPublisher "Seymour Shlien"
#define MyAppURL "ifdo.ca/~seymour/easy/"
#define MyAppExeName "easy_abc.exe"

#define MyBuildFolder "build\exe.win32-3.8"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{964A5677-C80C-47DB-A333-672AC7D7D70A}}
AppName={#MyAppName} {#MyAppVersion}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={commonpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile={#MyBuildFolder}\gpl-license.txt
OutputBaseFilename=EasyABC-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
Type: files; Name: "{app}\easy_abc.exe"
Type: files; Name: "{app}\easy_abc.zip"
Type: files; Name: "{app}\wx*.dll"
Type: files; Name: "{app}\*.pyd"
Type: files; Name: "{app}\easy_abc.exe.manifest"
Type: files; Name: "{app}\python27.dll"
Type: files; Name: "{app}\pywintypes27.dll"
Type: files; Name: "{app}\sqlite3.dll"
Type: files; Name: "{app}\library.zip"
Type: filesandordirs; Name: "{app}\Microsoft.VC90.CRT"

[Files]
Source: "{#MyBuildFolder}\easy_abc.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\gpl-license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\reference.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\python3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\python38.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\VCRUNTIME140.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\lib\*"; DestDir: "{app}\lib"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\bin\*"; DestDir: "{app}\bin\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\img\*"; DestDir: "{app}\img\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\locale\*"; DestDir: "{app}\locale\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\sound\*"; DestDir: "{app}\sound\"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
