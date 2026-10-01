# SPDX-License-Identifier: Apache-2.0

$projectRoot = Split-Path -Parent $PSScriptRoot
$temporaryDirectory = Join-Path $projectRoot 'build\tmp'

New-Item -ItemType Directory -Force $temporaryDirectory | Out-Null

$env:TEMP = $temporaryDirectory
$env:TMP = $temporaryDirectory

& $PSScriptRoot\prepare.ps1
python -m build $projectRoot
$version = (
    Select-String -Path (Join-Path $projectRoot 'pyproject.toml') -Pattern '^version = "(.+)"$'
).Matches.Groups[1].Value
$wheel = Join-Path $projectRoot "dist\tika_ape-$version-py3-none-any.whl"
$source = Join-Path $projectRoot "dist\tika_ape-$version.tar.gz"

python (Join-Path $PSScriptRoot 'normalize_archive.py') $wheel $source
