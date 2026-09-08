# Script de Snapshot Diario Local em PowerShell
# Gera arquivo zip em .snapshots/ e cria tag/branch no Git local
# PROIBIDO: git push

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SnapshotsDir = Join-Path $ProjectRoot ".snapshots"

if (!(Test-Path -Path $SnapshotsDir)) {
    New-Item -ItemType Directory -Path $SnapshotsDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ZipPath = Join-Path $SnapshotsDir "snapshot_$Timestamp.zip"

Write-Host "[*] Criando snapshot em: $ZipPath" -ForegroundColor Cyan

$Targets = @("src", "docs", "deploy", "configs", "scripts", "tests", "README.md", "setup.py", "requirements.txt", "Makefile", ".gitignore")
$ValidPaths = @()

foreach ($item in $Targets) {
    $fullPath = Join-Path $ProjectRoot $item
    if (Test-Path -Path $fullPath) {
        $ValidPaths += $fullPath
    }
}

Compress-Archive -Path $ValidPaths -DestinationPath $ZipPath -Force

$SizeMB = [math]::Round(((Get-Item $ZipPath).Length / 1MB), 2)
Write-Host "[+] Snapshot ZIP criado com sucesso: $ZipPath ($SizeMB MB)" -ForegroundColor Green

# Criar tag e branch local no Git
try {
    $TagName = "snapshot-$Timestamp"
    $BranchName = "backup/snapshot-$Timestamp"
    
    git tag -a $TagName -m "Snapshot automatico diario: $Timestamp"
    git branch $BranchName
    Write-Host "[+] Tag Git '$TagName' e branch '$BranchName' criadas localmente (sem push remoto)." -ForegroundColor Green
} catch {
    Write-Host "[!] Aviso ao registrar tag Git: $_" -ForegroundColor Yellow
}
