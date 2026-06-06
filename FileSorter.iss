; ============================================================
;  FileSorter — Inno Setup 6 Installer Script
;  Requires Inno Setup 6.x  https://jrsoftware.org/isdl.php
;
;  To compile:
;    ISCC.exe FileSorter.iss
;  Or just double-click FileSorter.iss after Inno Setup is installed.
;
;  Prerequisites before running this script:
;    1. Run create_installer.bat  (handles everything automatically), OR
;    2. Manually: run build.bat first so dist\FileSorter\ exists.
; ============================================================

#define MyAppName      "FileSorter"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "FileSorter"
#define MyAppExeName   "FileSorter.exe"
; PyInstaller onedir output — absolute path so ISCC finds it from any cwd
#define MyAppSrcDir    "C:\Users\19496\Downloads\New folder\dist\FileSorter"

; ── [Setup] ──────────────────────────────────────────────────────────────────

[Setup]
; A unique GUID for this application.  Do NOT reuse for a different app.
AppId={{B3E4F6A2-9C1D-4E7F-A3B2-C1D4E6F8A0B2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright=Copyright (C) 2026 {#MyAppPublisher}

; Install into %LOCALAPPDATA%\FileSorter — no admin rights required
DefaultDirName={localappdata}\{#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=

; Start Menu group
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=C:\Users\19496\Downloads\New folder\output
OutputBaseFilename=FileSorter_Setup
SetupIconFile=C:\Users\19496\Downloads\New folder\app_icon.ico

; Compression (lzma2/ultra64 gives the smallest size)
Compression=lzma2/ultra64
SolidCompression=yes
CompressionThreads=auto

; UI
WizardStyle=modern
ShowLanguageDialog=no
DisableDirPage=yes
DisableReadyPage=no
DisableFinishedPage=no

; Uninstall
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
CreateUninstallRegKey=yes

; Prevent running two copies during install
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no

; Minimum OS: Windows 10
MinVersion=10.0

; ── [Languages] ──────────────────────────────────────────────────────────────

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ── [Messages] ───────────────────────────────────────────────────────────────

[Messages]
WelcomeLabel1=Welcome to FileSorter
WelcomeLabel2=FileSorter is a native desktop file-sorting application.%n%nThis will install FileSorter {#MyAppVersion} on your computer.%n%nNo Python installation is required — everything is bundled.
FinishedHeadingLabel=FileSorter is ready
FinishedLabel=FileSorter has been installed on your computer.%n%nClick Finish to close this wizard.

; ── [Tasks] ──────────────────────────────────────────────────────────────────

[Tasks]
; Both shortcuts are checked by default (omitting Flags: checked — that is the default)
Name: "desktopicon";   Description: "Create a &desktop shortcut";    GroupDescription: "Shortcuts:"
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut"; GroupDescription: "Shortcuts:"

; ── [Files] ──────────────────────────────────────────────────────────────────

[Files]
; The entire PyInstaller onedir bundle (FileSorter.exe + all Qt/Python DLLs)
Source: "{#MyAppSrcDir}\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; Optional: install the icon separately so uninstall can remove it cleanly
;Source: "app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; ── [Icons] ──────────────────────────────────────────────────────────────────

[Icons]
; Start Menu
Name: "{autoprograms}\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{app}"; \
    Tasks: startmenuicon

; Desktop
Name: "{autodesktop}\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon

; ── [Registry] ───────────────────────────────────────────────────────────────

[Registry]
; Register in "Apps & Features" / "Add or Remove Programs"
Root: HKCU; \
    Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; \
    ValueType: string; ValueName: "InstallPath"; \
    ValueData: "{app}"; \
    Flags: uninsdeletekey

; ── [Run] — post-install ─────────────────────────────────────────────────────

[Run]
; Offer to launch FileSorter right after installation
Filename: "{app}\{#MyAppExeName}"; \
    Description: "Launch {#MyAppName} now"; \
    Flags: nowait postinstall skipifsilent

; ── [UninstallRun] ───────────────────────────────────────────────────────────

[UninstallRun]
; Make sure the app isn't running when uninstalling
Filename: "taskkill.exe"; \
    Parameters: "/f /im {#MyAppExeName}"; \
    Flags: runhidden skipifdoesntexist; \
    RunOnceId: "KillApp"

; ── [UninstallDelete] ────────────────────────────────────────────────────────

[UninstallDelete]
; Remove any files written at runtime (session config, sorter trash, etc.)
Type: filesandordirs; Name: "{app}"

; ── [Code] — custom wizard logic ─────────────────────────────────────────────

[Code]
// Detect if the app is already running before installing/uninstalling
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Kill any running instance silently
  Exec(ExpandConstant('{sys}\taskkill.exe'),
       '/f /im {#MyAppExeName}',
       '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  Exec(ExpandConstant('{sys}\taskkill.exe'),
       '/f /im {#MyAppExeName}',
       '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
