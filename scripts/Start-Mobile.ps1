param([string]$ApiUrl = "", [int]$Port = 8081, [switch]$Login, [switch]$Clear)
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
# Admite Node instalado normalmente o el runtime portátil disponible en este PC.
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    $nodeBin = Join-Path $env:USERPROFILE ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin"
    if (Test-Path (Join-Path $nodeBin "node.exe")) { $env:Path = "$nodeBin;$env:Path" }
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    $portableTools = Join-Path $env:USERPROFILE ".cache/isi-tools"
    if (Test-Path (Join-Path $portableTools "npm.cmd")) { $env:Path = "$portableTools;$env:Path" }
}
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) { throw "Instala Node.js LTS (incluye npm), vuelve a abrir PowerShell e intenta de nuevo." }
if (-not $ApiUrl) {
    $ip = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254*' } |
        Sort-Object @{Expression={if ($_.InterfaceAlias -like '*Wi-Fi*') {0} else {1}}} |
        Select-Object -First 1 -ExpandProperty IPAddress
    if ($ip) { $ApiUrl = "http://${ip}:8001" }
}
if ($ApiUrl) {
    $env:EXPO_PUBLIC_API_URL = $ApiUrl
    # Usa la misma interfaz de red para el QR y el backend cuando hay Wi-Fi y Ethernet.
    $apiHost = ([uri]$ApiUrl).Host
    if ($apiHost -notin @('localhost','127.0.0.1')) { $env:REACT_NATIVE_PACKAGER_HOSTNAME = $apiHost }
}
Push-Location (Join-Path $repo "mobile")
try {
    $needsInstall = -not (Test-Path "node_modules/expo/package.json")
    if (-not $needsInstall) {
        $installedExpo = (Get-Content "node_modules/expo/package.json" -Raw | ConvertFrom-Json).version
        $expectedExpo = (Get-Content "package.json" -Raw | ConvertFrom-Json).dependencies.expo
        $expectedMajor = [regex]::Match($expectedExpo, '\d+').Value
        $needsInstall = $installedExpo.Split('.')[0] -ne $expectedMajor
    }
    if ($needsInstall) {
        & $npm.Source ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias." }
    }
    Write-Host "Backend sugerido para la app: $ApiUrl"
    Write-Host "Mantén el backend abierto y conecta el teléfono al mismo Wi-Fi."
    if ($Login) {
        & $npm.Source exec -- expo login
        if ($LASTEXITCODE -ne 0) { throw "No se pudo iniciar sesion en Expo." }
    }
    if ($Clear) {
        & $npm.Source start -- --go --lan --port $Port --clear
    } else {
        & $npm.Source start -- --go --lan --port $Port
    }
} finally { Pop-Location }
