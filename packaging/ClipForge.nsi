Unicode true
RequestExecutionLevel user
ManifestSupportedOS all
ManifestDPIAware true
ManifestDPIAwareness PerMonitorV2,System
SetCompressor /SOLID lzma
SetCompressorDictSize 32

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"
!include "WinVer.nsh"

Name "ClipForge ${VERSION}"
Caption "ClipForge ${VERSION} Setup - UshaLabs"
OutFile "${SETUP_OUTPUT}"
InstallDir "$LOCALAPPDATA\ClipForge"
InstallDirRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ClipForge" "InstallLocation"
BrandingText "Developed by UshaLabs"
Icon "${ICON_PATH}"
UninstallIcon "${ICON_PATH}"

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "ClipForge"
VIAddVersionKey "CompanyName" "UshaLabs"
VIAddVersionKey "FileDescription" "ClipForge - Windows Setup Installer by UshaLabs"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2026 UshaLabs."

ShowInstDetails show
ShowUninstDetails show

!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "ClipForge by UshaLabs"
!define MUI_WELCOMEPAGE_TEXT "Welcome to the ClipForge Setup Wizard.$\r$\n$\r$\nClipForge turns long videos and live streams into captioned vertical clips locally on your PC, with automatic highlight selection, live buffer recording, and multi-platform publishing.$\r$\n$\r$\nInstall location defaults to a short path ($LOCALAPPDATA\ClipForge) for reliable speech-to-text and FFmpeg execution on Windows 10 and Windows 11 (x64)."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PROJECT_ROOT}\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_TITLE "ClipForge Installation Complete"
!define MUI_FINISHPAGE_TEXT "ClipForge has been installed on your computer.$\r$\n$\r$\nYou can open ClipForge from the Start Menu or Desktop shortcut."
!define MUI_FINISHPAGE_RUN "$INSTDIR\ClipForge.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ClipForge now"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Var Isolated
Var RegistryKey
Var Shortcut
Var Arguments
Var Result
Var Output
Var InstallSizeKB

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "ClipForge requires 64-bit Windows 10 or Windows 11."
    Abort
  ${EndIf}
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_ICONSTOP "ClipForge requires Windows 10 or Windows 11 (x64)."
    Abort
  ${EndIf}

  SetRegView 64
  SetShellVarContext current
  StrCpy $Isolated "0"

  ${GetParameters} $Arguments
  ClearErrors
  ${GetOptions} $Arguments "/ISOLATEDTEST" $Result
  ${IfNot} ${Errors}
    StrCpy $Isolated "1"
  ${EndIf}
FunctionEnd

Section "!ClipForge (Required)" SecMain
  SectionIn RO

  ${If} $Isolated != "1"
    nsExec::ExecToStack '"$SYSDIR\taskkill.exe" /IM ClipForge.exe'
    Pop $Result
    Pop $Output
    ${If} $Result == "0"
      Sleep 500
    ${EndIf}
    nsExec::ExecToStack '"$SYSDIR\taskkill.exe" /F /T /IM ClipForge.exe'
    Pop $Result
    Pop $Output
    Sleep 250
  ${EndIf}

  SetOutPath "$INSTDIR"
  SetOverwrite on

  !include "${INSTALL_FILES}"

  ${GetSize} "$INSTDIR" "/S=0K" $InstallSizeKB $0 $1
  WriteINIStr "$INSTDIR\clipforge-setup.ini" "Setup" "IsolatedTest" "$Isolated"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  SetOutPath "$INSTDIR"
  ${If} $Isolated == "1"
    StrCpy $RegistryKey "Software\Microsoft\Windows\CurrentVersion\Uninstall\ClipForge.PackagingTest"
    CreateDirectory "$INSTDIR\StartMenu"
    StrCpy $Shortcut "$INSTDIR\StartMenu\ClipForge.lnk"
    CreateShortcut "$Shortcut" "$INSTDIR\ClipForge.exe" "" "$INSTDIR\ClipForge.exe" 0
  ${Else}
    StrCpy $RegistryKey "Software\Microsoft\Windows\CurrentVersion\Uninstall\ClipForge"
    CreateDirectory "$SMPROGRAMS\UshaLabs"
    StrCpy $Shortcut "$SMPROGRAMS\UshaLabs\ClipForge.lnk"
    CreateShortcut "$Shortcut" "$INSTDIR\ClipForge.exe" "" "$INSTDIR\ClipForge.exe" 0
    CreateShortcut "$SMPROGRAMS\UshaLabs\Uninstall ClipForge.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  ${EndIf}

  WriteRegStr HKCU "$RegistryKey" "DisplayName" "ClipForge"
  WriteRegStr HKCU "$RegistryKey" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "$RegistryKey" "Publisher" "UshaLabs"
  WriteRegStr HKCU "$RegistryKey" "URLInfoAbout" "https://github.com/ushalabs/ClipForge"
  WriteRegStr HKCU "$RegistryKey" "HelpLink" "https://github.com/ushalabs/ClipForge"
  WriteRegStr HKCU "$RegistryKey" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "$RegistryKey" "DisplayIcon" "$INSTDIR\ClipForge.exe,0"
  WriteRegStr HKCU "$RegistryKey" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegStr HKCU "$RegistryKey" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
  WriteRegDWORD HKCU "$RegistryKey" "EstimatedSize" $InstallSizeKB
  WriteRegDWORD HKCU "$RegistryKey" "NoModify" 1
  WriteRegDWORD HKCU "$RegistryKey" "NoRepair" 1
SectionEnd

Section "Desktop Shortcut" SecDesktop
  ${If} $Isolated != "1"
    SetOutPath "$INSTDIR"
    CreateShortcut "$DESKTOP\ClipForge.lnk" "$INSTDIR\ClipForge.exe" "" "$INSTDIR\ClipForge.exe" 0
  ${EndIf}
SectionEnd

LangString DESC_SecMain ${LANG_ENGLISH} "Install the ClipForge desktop application and local runtime."
LangString DESC_SecDesktop ${LANG_ENGLISH} "Create a ClipForge shortcut on your Desktop."

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Function un.onInit
  SetRegView 64
  SetShellVarContext current
  ReadINIStr $Isolated "$INSTDIR\clipforge-setup.ini" "Setup" "IsolatedTest"
  ${If} $Isolated == "1"
    StrCpy $RegistryKey "Software\Microsoft\Windows\CurrentVersion\Uninstall\ClipForge.PackagingTest"
  ${Else}
    StrCpy $Isolated "0"
    StrCpy $RegistryKey "Software\Microsoft\Windows\CurrentVersion\Uninstall\ClipForge"
  ${EndIf}
FunctionEnd

Section "Uninstall"
  ${If} $Isolated != "1"
    nsExec::ExecToStack '"$SYSDIR\taskkill.exe" /IM ClipForge.exe'
    Pop $Result
    Pop $Output
    ${If} $Result == "0"
      Sleep 500
    ${EndIf}
    nsExec::ExecToStack '"$SYSDIR\taskkill.exe" /F /T /IM ClipForge.exe'
    Pop $Result
    Pop $Output
    Sleep 250
  ${EndIf}

  ${If} $Isolated == "1"
    Delete "$INSTDIR\StartMenu\ClipForge.lnk"
    RMDir "$INSTDIR\StartMenu"
  ${Else}
    Delete "$SMPROGRAMS\UshaLabs\ClipForge.lnk"
    Delete "$SMPROGRAMS\UshaLabs\Uninstall ClipForge.lnk"
    RMDir "$SMPROGRAMS\UshaLabs"
    Delete "$DESKTOP\ClipForge.lnk"
  ${EndIf}

  !include "${UNINSTALL_FILES}"
  Delete "$INSTDIR\clipforge-setup.ini"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  ReadRegStr $Result HKCU "$RegistryKey" "InstallLocation"
  ${If} $Result == "$INSTDIR"
    DeleteRegKey HKCU "$RegistryKey"
  ${EndIf}
SectionEnd
