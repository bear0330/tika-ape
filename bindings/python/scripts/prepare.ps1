# SPDX-License-Identifier: Apache-2.0

$projectRoot = Split-Path -Parent $PSScriptRoot
$repositoryRoot = Resolve-Path (Join-Path $projectRoot '..\..')
$packageRoot = Join-Path $projectRoot 'src\tika_ape'
$sourceApe = Join-Path $repositoryRoot 'tika.com'
$packageApe = Join-Path $packageRoot 'bin\tika.com'
$sourceConfig = Join-Path $repositoryRoot 'tika-config.json'
$packageConfig = Join-Path $packageRoot 'config\default.json'

& (Join-Path $repositoryRoot 'scripts\prepare.ps1')

New-Item -ItemType Directory -Force (Join-Path $packageRoot 'bin') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $packageRoot 'config') | Out-Null

if (-not (Test-Path $packageApe) -or
    (Get-FileHash $sourceApe).Hash -ne (Get-FileHash $packageApe).Hash) {
    Copy-Item $sourceApe $packageApe -Force
}

if (-not (Test-Path $packageConfig) -or
    (Get-FileHash $sourceConfig).Hash -ne (Get-FileHash $packageConfig).Hash) {
    Copy-Item $sourceConfig $packageConfig -Force
}

New-Item -ItemType Directory -Force (Join-Path $projectRoot 'tests\fixtures') | Out-Null
Copy-Item (Join-Path $repositoryRoot 'tests\fixtures\*') (Join-Path $projectRoot 'tests\fixtures') -Recurse -Force
