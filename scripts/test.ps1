# SPDX-License-Identifier: Apache-2.0

$repositoryRoot = Split-Path -Parent $PSScriptRoot

& $PSScriptRoot\prepare.ps1
python (Join-Path $repositoryRoot 'tests\test_tika_com.py')

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
