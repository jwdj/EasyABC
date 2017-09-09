; easyabcp07.nsi
;
; This script is based on example1.nsi, but it remember the directory, 
; has uninstall support and (optionally) installs start menu shortcuts.
;
; It will install example2.nsi into a directory that the user selects,

;--------------------------------

; The name of the installer
Name "easyabcp07 installer"

; The file to write
OutFile "easyabcp07_setup.exe"

; The default installation directory
InstallDir $PROGRAMFILES\easyabcp07

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\easyabcp07" "Install_Dir"

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "easyabcp07 (required)"

  SectionIn RO
  
 
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  

  File "easy_abc.exe"
  File "bz2.pyd"
  File "easy_abc.exe.manifest"
  File "easy_abc.zip"
  File "library.zip"
  File "pyexpat.pyd"
  File "python27.dll"
  File "pywintypes27.dll"
  File "reference.txt"
  File "select.pyd"
  File "sqlite3.dll"
  File "unicodedata.pyd"
  File "win32api.pyd"
  File "win32pipe.pyd"
  File "win32process.pyd"
  File "wx._controls_.pyd"
  File "wx._core_.pyd"
  File "wx._gdi_.pyd"
  File "wx._gizmos.pyd"
  File "wx._html.pyd"
  File "wx._media.pyd"
  File "wx._misc_.pyd"
  File "wx._stc.pyd"
  File "wx._windows_.pyd"
  File "wxbase30u_net_vc90.dll"
  File "wxbase30u_vc90.dll"
  File "wxmsw30u_adv_vc90.dll"
  File "wxmsw30u_core_vc90.dll"
  File "wxmsw30u_html_vc90.dll"
  File "wxmsw30u_media_vc90.dll"
  File "wxmsw30u_stc_vc90.dll"
  File "_ctypes.pyd"
  File "_elementtree.pyd"
  File "_hashlib.pyd"
  File "_socket.pyd"
  File "_sqlite3.pyd"
  File "_testcapi.pyd"
  File "_winxptheme.pyd"

  SetOutPath "$INSTDIR\bin"
  File /nonfatal /a /r "bin\"

  SetOutPath "$INSTDIR\img"
  File /nonfatal /a /r "img\"

  SetOutPath "$INSTDIR\locale"
  File /nonfatal /a /r "locale\"

  SetOutPath "$INSTDIR\Microsoft.VC90.CRT"
  File /nonfatal /a /r "Microsoft.VC90.CRT\"

  SetOutPath "$INSTDIR\sound"
  File /nonfatal /a /r "sound\"


  SetOutPath $INSTDIR

  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\NSIS_Example2 "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\easyabcp07" "DisplayName" "easyabcp07"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\easyabcp07" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\easyabcp07" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Example2" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\easyabcp07"
  CreateShortCut "$SMPROGRAMS\easyabcp07\easyabcp07.lnk" "$INSTDIR\easy_abc.exe" "" "$INSTDIR\easy_abc.exe" 0
  CreateShortCut "$SMPROGRAMS\easyabcp07\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  
SectionEnd

Section "Desktop Shortcut"
  CreateShortCut "$DESKTOP\EasyAbcp07.lnk" "$INSTDIR\easy_abc.exe" "" 
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\easyabcp07"
  DeleteRegKey HKLM SOFTWARE\easyabcp07

  ; Remove files and uninstaller
  Delete $INSTDIR\easyabc.exe
  RMDIR /r $INSTDIR\..\easyabcp07
  Delete $INSTDIR\uninstall.exe

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\easyabcp07\*.*"
  Delete "$DESKTOP\EasyAbcp07.lnk"

  ; Remove directories used
  RMDir "$SMPROGRAMS\easyabcp07"
  RMDir "$INSTDIR"

SectionEnd
