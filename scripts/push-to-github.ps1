# Envia o repositório local para o GitHub usando apenas git.
# Pré-requisito: repo vazio criado em https://github.com/new (privado ou público)
#               e git autenticado (Credential Manager, PAT ou SSH).
#
# Uso:
#   .\scripts\push-to-github.ps1 -GitHubUser SEU_USUARIO
#   .\scripts\push-to-github.ps1 -RemoteUrl https://github.com/SEU_USUARIO/app-mba-economia-fipe.git
#   .\scripts\push-to-github.ps1   # se origin já estiver configurado

param(
    [string]$GitHubUser = "",
    [string]$RepoName = "app-mba-economia-fipe",
    [string]$RemoteUrl = ""
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Get-ExistingRemote {
    $url = git remote get-url origin 2>$null
    if ($LASTEXITCODE -eq 0) { return $url.Trim() }
    return $null
}

$remote = Get-ExistingRemote

if (-not $remote) {
    if ($RemoteUrl) {
        $remote = $RemoteUrl.Trim()
    } elseif ($GitHubUser) {
        $remote = "https://github.com/$GitHubUser/$RepoName.git"
    } else {
        Write-Host @"
Remote 'origin' não configurado.

1. Crie um repo vazio em https://github.com/new (sem README/licença).
2. Execute um dos comandos:

   .\scripts\push-to-github.ps1 -GitHubUser SEU_USUARIO
   .\scripts\push-to-github.ps1 -RemoteUrl https://github.com/SEU_USUARIO/$RepoName.git
"@
        exit 1
    }

    git remote add origin $remote
    Write-Host "Remote origin: $remote"
} else {
    Write-Host "Remote origin já configurado: $remote"
}

git branch -M main

Write-Host "Enviando branch main..."
git push -u origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host @"

Push falhou. Verifique:
  - O repo existe no GitHub (vazio, sem commits iniciais conflitantes)
  - Suas credenciais git estão válidas (git credential manager ou SSH)
  - Permissão de escrita no repositório
"@
    exit 1
}

Write-Host ""
Write-Host "OK. Clone no Mac:"
Write-Host "  git clone $(Get-ExistingRemote)"
