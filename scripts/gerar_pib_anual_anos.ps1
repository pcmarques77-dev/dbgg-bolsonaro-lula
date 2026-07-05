# PIB anual Focus x IBGE 4T (2019-2026) + comparativos por periodo
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

foreach ($ano in 2019..2026) {
    Write-Host "=== PIB anual $ano ===" -ForegroundColor Cyan
    python -m mba_economia `
        --start-date 2019-01-01 `
        --out-dir output `
        --plot-mode none `
        --figure-extra pib-ano-trajetoria-ano `
        --ipca-mes-ano $ano
    if ($LASTEXITCODE -ne 0) { throw "Falha PIB anual $ano (exit $LASTEXITCODE)" }
}

Write-Host "=== PIB periodos (blocos) ===" -ForegroundColor Cyan
python -m mba_economia `
    --start-date 2019-01-01 `
    --out-dir output `
    --plot-mode none `
    --figure-extra pib-periodo-blocos

if ($LASTEXITCODE -ne 0) { throw "Falha PIB periodo-blocos" }
Write-Host "Concluido." -ForegroundColor Green
