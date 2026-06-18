; MarkItDown Desktop — Inno Setup Installer Script
; ───────────────────────────────────────────────────────
; This installer:
;   1. Installs the MarkItDown Desktop GUI application
;   2. Installs Python (if not present)
;   3. Installs the markitdown Python package and all dependencies
;   4. Creates Start Menu and Desktop shortcuts
;   5. Registers uninstaller
;
; Build with: iscc installer.iss
; Requires: Inno Setup 6+ (https://jrsoftware.org/issetup.php)
;
; IMPORTANT: Before building the installer, you must first:
;   1. Run: python build_exe.py        (builds the .exe via PyInstaller)
;   2. Ensure 'dist/MarkItDown Desktop/' exists with the bundled app
;   3. Place python-3.12.x-amd64.exe in the 'gui/redist/' folder

#define MyAppName "MarkItDown Desktop"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Microsoft Corporation"
#define MyAppURL "https://github.com/microsoft/markitdown"
#define MyAppExeName "MarkItDown Desktop.exe"
#define MyAppDescription "Convert documents to Markdown"

[Setup]
; Basic info
AppId={{8F3A9C47-2D1E-4B5F-A83C-1E9F2D4B6C78}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=installer_output
OutputBaseFilename=MarkItDown_Desktop_Setup_{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120,120
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDescription}
VersionInfoProductName={#MyAppName}
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "installpython"; Description: "Install Python 3.12 (required if Python is not already installed)"; GroupDescription: "Prerequisites:"; Flags: unchecked
Name: "installmarkitdown"; Description: "Install markitdown Python package and dependencies"; GroupDescription: "Prerequisites:"

[Files]
; Main application (PyInstaller output)
Source: "dist\MarkItDown Desktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Python installer (embedded for offline installation)
Source: "redist\python-3.12*.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall skipifsourcedoesntexist; Tasks: installpython

; pip requirements for markitdown
Source: "requirements_install.txt"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall; Tasks: installmarkitdown

; License
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

; README
Source: "..\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppDescription}"

[Run]
; Install Python silently (if user chose this task)
Filename: "{tmp}\python-3.12.7-amd64.exe"; Parameters: "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_tcltk=1"; StatusMsg: "Installing Python 3.12..."; Tasks: installpython; Flags: waituntilterminated

; Install markitdown via pip (if user chose this task)
Filename: "cmd.exe"; Parameters: "/c pip install ""markitdown[all]"" ttkbootstrap 2>&1 > ""{tmp}\markitdown_install.log"""; StatusMsg: "Installing MarkItDown and dependencies (this may take a few minutes)..."; Tasks: installmarkitdown; Flags: waituntilterminated runhidden

; Launch application after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// Check if Python is already installed
function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c python --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

// Warn user if Python is not found and they didn't select the install task
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpReady then
  begin
    if not IsPythonInstalled and not WizardIsTaskSelected('installpython') then
    begin
      MsgBox('Python does not appear to be installed on this system.' + #13#10 + #13#10 +
             'MarkItDown Desktop requires Python 3.10 or higher.' + #13#10 +
             'Please go back and check "Install Python 3.12" under Prerequisites,' + #13#10 +
             'or install Python manually from https://python.org', mbInformation, MB_OK);
    end;
  end;
end;

// Custom welcome message
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;
