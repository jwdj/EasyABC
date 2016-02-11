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
#define MyAppVersion "1.3.7.1"
#define MyAppPublisher "seymour shlien"
#define MyAppURL "ifdo.ca/~seymour/easy/"
#define MyAppExeName "easy_abc.exe"

#define MyBuildFolder "build\exe.win32-2.7"

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
DefaultDirName={pf}\{#MyAppName}-{#MyAppVersion}
DefaultGroupName={#MyAppName}
LicenseFile={#MyBuildFolder}\gpl-license.txt
OutputBaseFilename=setupEasy137
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyBuildFolder}\easy_abc.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\_ctypes.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\_elementtree.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\_hashlib.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\_socket.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\_sqlite3.pyd"; DestDir: "{app}"; Flags: ignoreversion
;Source: "{#MyBuildFolder}\_testcapi.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\_winxptheme.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\bz2.pyd"; DestDir: "{app}"; Flags: ignoreversion
;Source: "{#MyBuildFolder}\changes.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\easy_abc.exe.manifest"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\easy_abc.zip"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\gpl-license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\library.zip"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\pyexpat.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\python27.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\pywintypes27.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\reference.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\select.pyd"; DestDir: "{app}"; Flags: ignoreversion
;Source: "{#MyBuildFolder}\setup.iss"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\sqlite3.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\unicodedata.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\win32api.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\win32pipe.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\win32process.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._controls_.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._core_.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._gdi_.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._gizmos.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._html.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._media.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._misc_.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._stc.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wx._windows_.pyd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wxbase30u_net_vc90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wxbase30u_vc90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wxmsw30u_adv_vc90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wxmsw30u_core_vc90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wxmsw30u_html_vc90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wxmsw30u_media_vc90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\wxmsw30u_stc_vc90.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyBuildFolder}\bin\*"; DestDir: "{app}\bin\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\img\*"; DestDir: "{app}\img\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\locale\da\*"; DestDir: "{app}\locale\da\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\locale\fr\*"; DestDir: "{app}\locale\fr\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\locale\it\*"; DestDir: "{app}\locale\it\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\locale\nl\*"; DestDir: "{app}\locale\nl\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\locale\ja\*"; DestDir: "{app}\locale\ja\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\locale\sv\*"; DestDir: "{app}\locale\sv\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\Microsoft.VC90.CRT\*"; DestDir: "{app}\Microsoft.VC90.CRT\"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#MyBuildFolder}\sound\*"; DestDir: "{app}\sound\"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
