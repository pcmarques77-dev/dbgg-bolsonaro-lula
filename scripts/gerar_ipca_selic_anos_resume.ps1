# Retoma IPCA + Selic 2022-2026 + cruzamento
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

foreach ($ano in 2022..2026) {
    Write-Host "=== Ano $ano ===" -ForegroundColor Cyan
    python -m mba_economia `
        --start-date 2019-01-01 `
        --out-dir output `
        --plot-mode none `
        --figure-extra ipca-mes-piloto-ano `
        --figure-extra ipca-anual-trajetoria-ano `
        --figure-extra selic-mes-piloto-ano `
        --figure-extra selic-anual-trajetoria-ano `
        --ipca-mes-ano $ano
    if ($LASTEXITCODE -ne 0) { throw "Falha no ano $ano (exit $LASTEXITCODE)" }
}

Write-Host "=== Cruzamento IPCA x Selic ===" -ForegroundColor Cyan
python -m mba_economia `
    --start-date 2019-01-01 `
    --out-dir output `
    --plot-mode none `
    --figure-extra ipca-selic-cross-comparativo

if ($LASTEXITCODE -ne 0) { throw "Falha no cruzamento IPCA x Selic" }
Write-Host "Concluido." -ForegroundColor Green
