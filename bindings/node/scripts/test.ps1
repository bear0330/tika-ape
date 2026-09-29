# SPDX-License-Identifier: Apache-2.0

function Invoke-NodeTest([string]$testPath) {
    node $testPath

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

& $PSScriptRoot\prepare.ps1

Invoke-NodeTest (Join-Path $PSScriptRoot '..\tests\test_tika_ape.mjs')
Invoke-NodeTest (Join-Path $PSScriptRoot '..\tests\test_host_services.mjs')
Invoke-NodeTest (Join-Path $PSScriptRoot '..\tests\test_legacy.mjs')
