# SPDX-License-Identifier: Apache-2.0

$projectRoot = Split-Path -Parent $PSScriptRoot
$repositoryRoot = Resolve-Path (Join-Path $projectRoot '..\..')
$sourceConfig = Join-Path $repositoryRoot 'tika-config.json'
$packageConfig = Join-Path $projectRoot 'src\config\default.json'

& (Join-Path $repositoryRoot 'scripts\prepare.ps1')

New-Item -ItemType Directory -Force (Join-Path $projectRoot 'src\bin') | Out-Null
Copy-Item (Join-Path $repositoryRoot 'tika.com') (Join-Path $projectRoot 'src\bin\tika.com') -Force

New-Item -ItemType Directory -Force (Join-Path $projectRoot 'src\config') | Out-Null

if (-not (Test-Path $packageConfig) -or
    (Get-FileHash $sourceConfig).Hash -ne (Get-FileHash $packageConfig).Hash) {
    Copy-Item $sourceConfig $packageConfig -Force
}

New-Item -ItemType Directory -Force (Join-Path $projectRoot 'tests\fixtures') | Out-Null
Copy-Item (Join-Path $repositoryRoot 'tests\fixtures\*') (Join-Path $projectRoot 'tests\fixtures') -Recurse -Force
