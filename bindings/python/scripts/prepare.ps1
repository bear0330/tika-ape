# SPDX-License-Identifier: Apache-2.0

$projectRoot = Split-Path -Parent $PSScriptRoot
$repositoryRoot = Resolve-Path (Join-Path $projectRoot '..\..')
$packageRoot = Join-Path $projectRoot 'src\tika_ape'
$sourceApe = Join-Path $repositoryRoot 'tika.com'
$packageApe = Join-Path $packageRoot 'bin\tika.com'

& (Join-Path $repositoryRoot 'scripts\prepare.ps1')

New-Item -ItemType Directory -Force (Join-Path $packageRoot 'bin') | Out-Null

if (-not (Test-Path $packageApe) -or
    (Get-FileHash $sourceApe).Hash -ne (Get-FileHash $packageApe).Hash) {
    Copy-Item $sourceApe $packageApe -Force
}

New-Item -ItemType Directory -Force (Join-Path $projectRoot 'tests\fixtures') | Out-Null
Copy-Item (Join-Path $repositoryRoot 'tests\fixtures\*') (Join-Path $projectRoot 'tests\fixtures') -Recurse -Force
