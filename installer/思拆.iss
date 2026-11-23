; 思拆 Windows 安装包脚本
; 安装到当前用户目录，无需管理员权限；创建桌面/开始菜单快捷方式；安装时写入 .env。

#define MyAppName "思拆"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "思拆"
#define MyAppExeName "思拆.exe"
#define SourceDir "C:\Users\21857\Desktop\siche\dist\思拆"

[Setup]
AppId={{8D4F0F0A-2A7B-4C1E-9B3A-6F0C1D2E3A4B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=C:\Users\21857\Desktop
OutputBaseFilename=思拆-安装包
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
SetupLogging=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no
VersionInfoVersion=3.0.0.0

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"; Flags: checkedonce

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".env,siche.db,siche.log,*.log"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\.env"

[Code]
var
  KeyPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  KeyPage := CreateInputQueryPage(wpSelectTasks,
    'DeepSeek 配置',
    '输入你的 DeepSeek API Key',
    '用于调用 deepseek-flash。留空也可以，安装后可在程序目录的 .env 中填写。');
  KeyPage.Add('API Key:', False);
  KeyPage.Values[0] := ExpandConstant('{%SICHE_DEEPSEEK_API_KEY}');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Key: String;
  Content: String;
begin
  if CurStep = ssPostInstall then
  begin
    Key := Trim(KeyPage.Values[0]);
    if Key = '' then
      Key := ExpandConstant('{%SICHE_DEEPSEEK_API_KEY}');
    Content :=
      'SICHE_DEEPSEEK_API_KEY=' + Key + #13#10 +
      'SICHE_DEEPSEEK_BASE_URL=https://api.deepseek.com' + #13#10 +
      'SICHE_DEEPSEEK_MODEL=deepseek-flash' + #13#10 +
      'SICHE_DEEPSEEK_TIMEOUT=60' + #13#10 +
      'SICHE_DEEPSEEK_MAX_TOKENS=3000' + #13#10 +
      'SICHE_HISTORY_LIMIT=12' + #13#10;
    SaveStringToFile(ExpandConstant('{app}\.env'), Content, False);
  end;
end;
