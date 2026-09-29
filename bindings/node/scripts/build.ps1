# SPDX-License-Identifier: Apache-2.0

$projectRoot = Split-Path -Parent $PSScriptRoot
$cacheDirectory = Join-Path $projectRoot 'build\npm-cache'

New-Item -ItemType Directory -Force $cacheDirectory | Out-Null

& $PSScriptRoot\prepare.ps1
Push-Location $projectRoot
npm pack --cache $cacheDirectory
Pop-Location
