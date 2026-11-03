param([int]$Port = 8001, [string]$Database = "campeonato_prueba_manual.sqlite3")
$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$backend = Join-Path $repo "backend"
$python = Join-Path $backend ".venv/Scripts/python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Crea primero el entorno virtual de backend e instala requirements-dev.txt." }
Push-Location $backend
try {
    # La prueba usa un archivo local explícito, sin editar la configuración .env.
    $dbPath = [IO.Path]::GetFullPath((Join-Path $backend $Database)).Replace('\','/')
    $env:DATABASE_URL = "sqlite:///$dbPath"
    & $python -m app.create_tables
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron preparar las tablas." }
    Write-Host "Web en este computador: http://127.0.0.1:$Port"
    Write-Host "Direcciones para la app móvil (usa la red Wi-Fi del teléfono):"
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -ne "127.0.0.1" -and $_.IPAddress -notlike "169.254*" } |
        ForEach-Object { Write-Host "  $($_.InterfaceAlias): http://$($_.IPAddress):$Port" }
    Write-Host "Si la base es nueva, crea el primer administrador con python -m app.bootstrap_admin."
    & $python -m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload
} finally { Pop-Location }
