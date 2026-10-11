; installer.iss
; Inno Setup script for the Ittefaq Plastic Industries Stock & Invoice Manager.
;
; Build with:
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer.iss
; (run PyInstaller first so dist\StockInvoiceManager.exe exists)
;
; This is a PER-USER install (PrivilegesRequired=lowest), installing into
; %LOCALAPPDATA%\Programs. That is deliberate, not a shortcut: the app keeps
; its database, invoice PDFs and backups in a "data" folder right beside its
; own .exe, so the install folder MUST stay writable by the person running
; the app. Program Files is not writable without elevation, so installing
; there would make the app fail at startup the moment it tried to create
; that data folder.

; AppName is what the wizard, Start Menu group and shortcuts show.
; AppExeName stays "StockInvoiceManager.exe" deliberately — it is an
; internal filename the owner never sees, and keeping it stable avoids
; churning the .spec, the [Files]/[Icons] references and the existing
; install's upgrade path.
#define AppName "Ittefaq Plastic Industries - Stock & Invoice Manager"
#define AppShortName "Ittefaq Stock & Invoice Manager"
#define AppExeName "StockInvoiceManager.exe"
#define AppVersion "1.0.0"
#define AppPublisher "Ittefaq Plastic Industries"

[Setup]
; AppId must stay fixed forever — it is how Windows recognises an existing
; install for upgrades/uninstall. Changing it creates duplicate entries.
AppId={{8F3A9C21-4B7D-4E58-9A16-2C5D7E8F1B34}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\StockInvoiceManager
; Start Menu folder is grouped under the company, the usual Windows convention.
DefaultGroupName={#AppPublisher}
DisableProgramGroupPage=yes
; Per-user install: no UAC prompt, and the install folder stays writable.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist\installer
OutputBaseFilename=IttefaqPlasticIndustries-StockInvoiceManager-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Shows the app's own embedded icon in Apps & Features.
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; ONLY the executable ships. The data folder is deliberately NOT bundled —
; a fresh install must start with an empty database that the app creates
; itself on first run.
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; No IconFilename is given, so each shortcut uses the icon embedded in the
; .exe itself.
; Shortcuts use the shorter name so they stay readable on the Desktop and
; in the Start Menu; the full name is kept for the wizard and Apps & Features.
Name: "{group}\{#AppShortName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Invoice Data Folder"; Filename: "{app}\data"; Comment: "Where the database, invoice PDFs and daily backups are kept — copy this whole folder to back up."
Name: "{group}\{cm:UninstallProgram,{#AppShortName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppShortName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppShortName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; NOTE: there is no [UninstallDelete] section on purpose. Uninstalling removes
; only the files this installer put there — the "data" folder the app created
; at runtime (database, invoices, backups) is left untouched, so uninstalling
; or reinstalling can never destroy the business's records.
