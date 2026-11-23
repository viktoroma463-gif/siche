$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
Set-Location $Root

$ApiPort = if ($env:SICHE_API_PORT) { $env:SICHE_API_PORT } else { "8010" }
$WebPort = if ($env:SICHE_WEB_PORT) { $env:SICHE_WEB_PORT } else { "5174" }

function Resolve-SichePython {
  $candidates = @()
  if (Get-Command py -ErrorAction SilentlyContinue) {
    $candidates += @{ Name = "py"; Args = @("-3") }
  }
  foreach ($cmd in @("python", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
      $candidates += @{ Name = $cmd; Args = @() }
    }
  }
  $paths = @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:ProgramFiles\Python313\python.exe",
    "$env:ProgramFiles\Python312\python.exe",
    "$env:ProgramFiles\Python311\python.exe",
    "C:\Python313\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe"
  )
  foreach ($p in $paths) {
    if (Test-Path $p) { $candidates += @{ Name = $p; Args = @() } }
  }
  foreach ($c in $candidates) {
    try {
      $ver = & $c.Name @($c.Args + @("-c", "import sys; print(sys.version_info>= (3,10))")) 2>$null
      if ($ver -match "True") { return $c }
    } catch { }
  }
  throw "未找到 Python 3.10+。请安装后确保 py 或 python 可用。"
}

$Py = Resolve-SichePython
$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
  & $Py.Name @($Py.Args + @("-m", "venv", (Join-Path $Root ".venv")))
}
& $VenvPy -m pip install -q -r (Join-Path $Root "backend\requirements.txt")

if (-not (Test-Path (Join-Path $Root "frontend\node_modules"))) {
  Push-Location (Join-Path $Root "frontend")
  npm install
  Pop-Location
}

$env:PYTHONPATH = Join-Path $Root "backend"
Write-Host "思拆 API  →  http://127.0.0.1:${ApiPort}/"
Write-Host "思拆 界面 →  http://127.0.0.1:${WebPort}/"

$api = Start-Process -FilePath $VenvPy -ArgumentList @("-m", "uvicorn", "app.main:app", "--app-dir", (Join-Path $Root "backend"), "--host", "127.0.0.1", "--port", $ApiPort) -PassThru -NoNewWindow
$web = Start-Process -FilePath "npm" -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", $WebPort) -WorkingDirectory (Join-Path $Root "frontend") -PassThru -NoNewWindow

try {
  Wait-Process -Id $api.Id, $web.Id
} finally {
  if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue }
  if ($web -and -not $web.HasExited) { Stop-Process -Id $web.Id -Force -ErrorAction SilentlyContinue }
}
