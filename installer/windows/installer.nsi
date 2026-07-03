; NSIS Installer Script for Live Translation
; This script creates a Windows installer for the Live Translation application

; Modern UI
!include "MUI2.nsh"

; Application Information
; APP_NAME and APP_VERSION are passed as command-line parameters from build-installer.ps1
; Usage: makensis /DAPP_NAME=LiveTranslation /DAPP_VERSION=1.0.0 installer.nsi
!ifndef APP_NAME
    !define APP_NAME "LiveTranslation"  ; Fallback name if not provided
!endif
!ifndef APP_VERSION
    !define APP_VERSION "1.0.0"  ; Fallback version if not provided
!endif
!define APP_PUBLISHER "Matthias Kuczera, Raimund Hummel"
!define APP_WEB_SITE "https://github.com/RaHummel/live-translation"
!define APP_EXE "${APP_NAME}.exe"
!define APP_UNINSTALLER "uninstall.exe"

; Installer Information
Name "${APP_NAME}"
OutFile "..\..\dist\installers\LiveTranslation-${APP_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "..\..\img\live-translation-app.ico"
!define MUI_UNICON "..\..\img\live-translation-app.ico"

; Pages
!insertmacro MUI_PAGE_LICENSE "..\\..\\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "German"

; Version Information
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "Live Translation Installer"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "© 2024 ${APP_PUBLISHER}"

; Installer Sections
Section "!${APP_NAME}" SEC01
    SectionIn RO
    SetOutPath "$INSTDIR"
    SetOverwrite on
    
    ; Copy all files from dist directory
    File /r "..\..\dist\${APP_NAME}\*.*"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\${APP_UNINSTALLER}"
    
    ; Write registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\${APP_NAME}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_WEB_SITE}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\${APP_UNINSTALLER}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\${APP_UNINSTALLER}"
SectionEnd

; Optional Desktop Shortcut Section
Section "Desktop Shortcut" SEC02
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove files and directories
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts (both Start Menu and Desktop if they exist)
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"
SectionEnd

; Section Descriptions
LangString DESC_SEC01 ${LANG_ENGLISH} "Install ${APP_NAME} application files"
LangString DESC_SEC01 ${LANG_GERMAN} "Installiert die ${APP_NAME} Anwendungsdateien"

LangString DESC_SEC02 ${LANG_ENGLISH} "Create a shortcut on the desktop"
LangString DESC_SEC02 ${LANG_GERMAN} "Erstellt eine Verknuepfung auf dem Desktop"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} $(DESC_SEC01)
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC02} $(DESC_SEC02)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
