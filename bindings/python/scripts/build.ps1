# SPDX-License-Identifier: Apache-2.0

$projectRoot = Split-Path -Parent $PSScriptRoot
$temporaryDirectory = Join-Path $projectRoot 'build\tmp'

New-Item -ItemType Directory -Force $temporaryDirectory | Out-Null

$env:TEMP = $temporaryDirectory
$env:TMP = $temporaryDirectory

& $PSScriptRoot\prepare.ps1
python -m build $projectRoot
