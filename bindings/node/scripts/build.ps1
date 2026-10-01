# SPDX-License-Identifier: Apache-2.0

$projectRoot = Split-Path -Parent $PSScriptRoot
$cacheDirectory = Join-Path $projectRoot 'build\npm-cache'

New-Item -ItemType Directory -Force $cacheDirectory | Out-Null

& $PSScriptRoot\prepare.ps1
Push-Location $projectRoot
npm pack --cache $cacheDirectory
Pop-Location

$version = (Get-Content (Join-Path $projectRoot 'package.json') -Raw | ConvertFrom-Json).version
$archive = Join-Path $projectRoot "tika-ape-$version.tgz"

node (Join-Path $PSScriptRoot 'normalize_tarball.mjs') $archive
