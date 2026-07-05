# Script de Export Unificado para IAs (Gemini / NotebookLM)
# Copia todos os dados relevantes do projeto para output/exportacao_ia_v2/

$ErrorActionPreference = "Stop"
$projectRoot = "c:\Users\pcmar\app-mba-economia-fipe"
$exportDir = "$projectRoot\output\exportacao_ia_v2"
$publicData = "$projectRoot\v2\pib-focus-viz\public\data"

Write-Host "=== Export Unificado TCC MBA FIPE ===" -ForegroundColor Cyan
Write-Host "Destino: $exportDir" -ForegroundColor Yellow

# Criar subpastas
New-Item -ItemType Directory -Force -Path "$exportDir\dados" | Out-Null
New-Item -ItemType Directory -Force -Path "$exportDir\econometria" | Out-Null

Write-Host "`n[1/4] Copiando dados descritivos (CSVs)..." -ForegroundColor Green
$dadosFiles = @(
    "painel_focus_mvp.csv",
    "comparacao_ipca_ano_fechamento.csv",
    "comparacao_ipca_mensal.csv",
    "comparacao_ipca_mensal_inicial.csv",
    "comparacao_ipca_ano_calendario.csv",
    "comparacao_selic_ano_fechamento.csv",
    "comparacao_selic_mensal.csv",
    "comparacao_selic_ano_calendario.csv",
    "comparacao_pib_ano_fechamento.csv",
    "comparacao_pib_ano_calendario.csv",
    "comparacao_focus_dbgg.csv",
    "comparacao_focus_ibge_pib_trimestral.csv",
    "metadados_series.csv"
)

$copied = 0
foreach ($f in $dadosFiles) {
    $src = "$publicData\$f"
    if (Test-Path $src) {
        Copy-Item $src "$exportDir\dados\$f" -Force
        $copied++
    } else {
        Write-Host "  [SKIP] $f nao encontrado" -ForegroundColor DarkYellow
    }
}
Write-Host "  $copied arquivos copiados para dados/" -ForegroundColor White

Write-Host "`n[2/4] Copiando outputs econometricos..." -ForegroundColor Green
$econFiles = Get-ChildItem "$publicData\econometria_ols_*" -File
$copied = 0
foreach ($f in $econFiles) {
    Copy-Item $f.FullName "$exportDir\econometria\$($f.Name)" -Force
    $copied++
}
Write-Host "  $copied arquivos copiados para econometria/" -ForegroundColor White

Write-Host "`n[3/4] Copiando metodologia..." -ForegroundColor Green
$metodoSrc = "$projectRoot\output\exportacao_ia_2021\metodologia_calculo_ipca.md"
if (Test-Path $metodoSrc) {
    Copy-Item $metodoSrc "$exportDir\metodologia_calculo_ipca.md" -Force
    Write-Host "  metodologia_calculo_ipca.md copiado" -ForegroundColor White
}

Write-Host "`n[4/4] Verificando relatorio e README..." -ForegroundColor Green
if (Test-Path "$exportDir\relatorio_completo_tcc.md") {
    Write-Host "  relatorio_completo_tcc.md OK" -ForegroundColor White
} else {
    Write-Host "  [ERRO] relatorio_completo_tcc.md nao encontrado!" -ForegroundColor Red
}
if (Test-Path "$exportDir\README_para_ia.md") {
    Write-Host "  README_para_ia.md OK" -ForegroundColor White
}

# Resumo final
Write-Host "`n=== EXPORT CONCLUIDO ===" -ForegroundColor Cyan
$totalFiles = (Get-ChildItem $exportDir -Recurse -File).Count
$totalSizeMB = [math]::Round(((Get-ChildItem $exportDir -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB), 2)
Write-Host "Total: $totalFiles arquivos | ${totalSizeMB} MB" -ForegroundColor Yellow
Write-Host "Pasta: $exportDir" -ForegroundColor Yellow
Write-Host "`nProximos passos:" -ForegroundColor White
Write-Host "  1. Abra o Gemini/NotebookLM" -ForegroundColor White
Write-Host "  2. Carregue relatorio_completo_tcc.md (documento principal)" -ForegroundColor White
Write-Host "  3. Carregue os CSVs de dados/ e econometria/ conforme necessidade" -ForegroundColor White
Write-Host "  4. Use README_para_ia.md como guia de referencia" -ForegroundColor White
