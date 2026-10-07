# build.ps1
# Baut Menu-Edit.py als EINE windowed-EXE (PyInstaller) in einem
# eigenen venv (keine globale Python-Umgebung, AGENTS.md §7).
#
# Aufruf:  powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1
#          (oder build.bat aus cmd)
# Ergebnis: dist\Menu-Edit.exe  (+ Exitcode 0 bei Erfolg, 1 bei Fehler)
#
# Idempotent: vorhandenes venv wird wiederverwendet, alte Artefakte
# werden vor dem Build entfernt.

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir     = Join-Path $ProjectRoot "venv-build"
$DistDir     = Join-Path $ProjectRoot "dist"
$BuildDir    = Join-Path $ProjectRoot "build"
$Script      = Join-Path $ProjectRoot "Menu-Edit.py"
$IconsDir    = Join-Path $ProjectRoot "icons"
$Icon        = Join-Path $IconsDir "menu-editor.ico"
$ExePath     = Join-Path $DistDir "Menu-Edit.exe"
$VenvPython  = Join-Path $VenvDir "Scripts\python.exe"

Write-Host "=== Menu-Edit Build ==="

# 0) Vorbedingungen pruefen
if (-not (Test-Path $Script)) {
    Write-Host "FEHLER: Menu-Edit.py nicht gefunden: $Script"
    exit 1
}
if (-not (Test-Path $Icon)) {
    Write-Host "FEHLER: EXE-Icon nicht gefunden: $Icon"
    exit 1
}

$pythonVersion = & python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: python nicht gefunden (PATH pruefen)."
    exit 1
}
Write-Host "Python: $pythonVersion"

# 1) Eigenes venv anlegen (falls nicht vorhanden) — wird immer
#    wiederverwendet, nie die globale Umgebung angetastet.
if (-not (Test-Path $VenvPython)) {
    Write-Host "Erstelle Build-venv: $VenvDir"
    & python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FEHLER: venv-Erstellung fehlgeschlagen (Exit $LASTEXITCODE)."
        exit 1
    }
} else {
    Write-Host "Build-venv vorhanden: $VenvDir"
}

# 2) Build-Abhaengigkeit installieren (idempotent): PyInstaller
Write-Host "Installiere/aktualisiere PyInstaller im venv ..."
& $VenvPython -m pip install --disable-pip-version-check --quiet --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: pip-Installation von PyInstaller fehlgeschlagen (Exit $LASTEXITCODE)."
    exit 1
}
$pyiVersion = & $VenvPython -m PyInstaller --version
Write-Host "PyInstaller: $pyiVersion"

# 3) Alte Artefakte entfernen (idempotenter Neuaufbau)
foreach ($stale in @($ExePath, (Join-Path $BuildDir "Menu-Edit"))) {
    if (Test-Path $stale) {
        Remove-Item $stale -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 4) One-File-Build (windowed, mit eingebetteten Icons + EXE-Icon)
Write-Host "Baue Menu-Edit.exe (One-File, windowed) ..."
& $VenvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --uac-admin `
    --name "Menu-Edit" `
    --icon "$Icon" `
    --add-data "$IconsDir;icons" `
    --distpath $DistDir `
    --workpath $BuildDir `
    --specpath $BuildDir `
    $Script

if ($LASTEXITCODE -ne 0) {
    Write-Host "FEHLER: PyInstaller-Build fehlgeschlagen (Exit $LASTEXITCODE)."
    exit 1
}

# 5) Ergebnis pruefen und melden
if (Test-Path $ExePath) {
    # sha.txt: SHA-256, Name und Datum/Uhrzeit der
    # gerade erstellten EXE (wird bei jedem Build
    # neu geschrieben).
    $exeItem  = Get-Item $ExePath
    $hash     = (Get-FileHash $ExePath -Algorithm SHA256).Hash
    $created  = $exeItem.LastWriteTime.ToString("dd.MM.yyyy HH:mm:ss")
    $ShaPath  = Join-Path $DistDir "sha.txt"
    @(
        "Datei: $($exeItem.Name)"
        "SHA-256: $hash"
        "Erstellt: $created"
    ) | Set-Content -Path $ShaPath -Encoding UTF8

    $size = [math]::Round($exeItem.Length / 1MB, 1)
    Write-Host "SHA-256: $hash"
    Write-Host "sha.txt geschrieben: $ShaPath"
    Write-Host "=== ERFOLG: $ExePath ($size MB) ==="
    exit 0
}

Write-Host "FEHLER: Build meldete Erfolg, aber $ExePath fehlt."
exit 1
