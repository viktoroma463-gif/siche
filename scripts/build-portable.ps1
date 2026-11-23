$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
Set-Location $Root

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) { throw "未找到 .venv，请先运行 scripts\dev.ps1 完成环境安装。" }

Write-Host "Installing PyInstaller..."
& $VenvPy -m pip install -q "pyinstaller>=6.0"
if ($LASTEXITCODE -ne 0) { throw "pip install pyinstaller failed" }

$DistJs = Join-Path $Root "frontend\dist\index.html"
if (-not (Test-Path $DistJs)) {
  if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "未找到 npm，且 frontend/dist 不存在。" }
  Push-Location (Join-Path $Root "frontend")
  if (-not (Test-Path "node_modules")) { npm install }
  npm run build
  if ($LASTEXITCODE -ne 0) { Pop-Location; throw "frontend build failed" }
  Pop-Location
}

$OutName = "思拆"
$PyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"
$DataSep = ";"
$AddData = "frontend\dist${DataSep}web"

Write-Host "Packaging $OutName.exe ..."
& $PyInstaller --noconfirm --clean --onedir --noconsole --name $OutName `
  --paths (Join-Path $Root "backend") `
  --add-data $AddData `
  --hidden-import app `
  --hidden-import app.main `
  --hidden-import app.desktop `
  --hidden-import app.engine `
  --hidden-import app.prompts `
  --hidden-import app.rules.delegation `
  --hidden-import app.rules.copy_lock `
  --hidden-import app.config `
  --hidden-import app.store `
  --hidden-import app.schemas `
  --hidden-import app.llm `
  --hidden-import uvicorn `
  --hidden-import uvicorn.logging `
  --hidden-import uvicorn.loops.auto `
  --hidden-import uvicorn.protocols.http.auto `
  --hidden-import uvicorn.protocols.http.h11_impl `
  --hidden-import uvicorn.protocols.websockets.auto `
  --hidden-import uvicorn.lifespan.on `
  --collect-all uvicorn `
  --collect-all starlette `
  --collect-all fastapi `
  --collect-all pydantic `
  --collect-all pydantic_settings `
  --collect-all anyio `
  --exclude-module pytest `
  --exclude-module watchfiles `
  (Join-Path $Root "backend\app\desktop.py")

if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$PackDir = Join-Path $Root "dist\$OutName"
$Readme = @"
思拆（绿色版 · 统一版）

使用方法
1. 请解压整个文件夹，不要只单独把「思拆.exe」拷走。
2. 把本目录里的 .env.example 复制为 .env，填写 SICHE_DEEPSEEK_API_KEY。
3. 双击「思拆.exe」，先看 3 秒闪屏，随后自动进入协作界面。
4. 若 Windows 弹出「已保护你的电脑」或安全提示，请点「更多信息」→「仍要运行」。这是因为本程序未做代码签名，并不是病毒。
5. 用完后关闭「思拆」小窗口即可退出。不要只关浏览器，否则后台仍在运行。

数据说明
- 会话、规划单、微测试作答保存在本目录的 siche.db。
- 导出会话会在浏览器下载 HTML 与 JSON 两份文件。
- 包内不包含任何 API Key，接收方需填自己的密钥。

未配置密钥时仍可打开界面，但无法发起对话。
DeepSeek 官方 API 不带联网搜索，文献线索由模型知识生成，一律标注【待核验】。
"@
[System.IO.File]::WriteAllText((Join-Path $PackDir "使用说明.txt"), $Readme, [System.Text.UTF8Encoding]::new($true))
Copy-Item (Join-Path $Root ".env.example") (Join-Path $PackDir ".env.example") -Force
Copy-Item (Join-Path $Root "docs\使用说明.md") (Join-Path $PackDir "使用说明.md") -Force
Copy-Item (Join-Path $Root "docs\产品与功能总览.md") (Join-Path $PackDir "产品与功能总览.md") -Force

$ZipPath = Join-Path $env:USERPROFILE "Desktop\思拆-绿色版.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
if (Test-Path (Join-Path $Root "dist\思拆-绿色版.zip")) { Remove-Item (Join-Path $Root "dist\思拆-绿色版.zip") -Force }

$Stage = Join-Path $Root "dist\siche-portable-stage"
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $Stage "思拆") | Out-Null
Copy-Item -Path (Join-Path $PackDir "*") -Destination (Join-Path $Stage "思拆") -Recurse -Force

# Prefer tar for fewer Windows path issues; fallback to Compress-Archive
$PortableZip = Join-Path $Root "dist\思拆-绿色版.zip"
Push-Location $Stage
tar -a -cf $PortableZip "思拆"
if ($LASTEXITCODE -ne 0) {
  Compress-Archive -Path (Join-Path $Stage "思拆") -DestinationPath $PortableZip -Force
}
Pop-Location

Copy-Item $PortableZip $ZipPath -Force
Write-Host "PACK_OK $ZipPath"
Get-Item $ZipPath, $PortableZip | Select-Object FullName, Length, LastWriteTime
