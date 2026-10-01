# SPDX-License-Identifier: Apache-2.0

function Invoke-PythonTest([string]$testPath) {
    python $testPath

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

& $PSScriptRoot\prepare.ps1

Invoke-PythonTest (Join-Path $PSScriptRoot '..\tests\test_tika_ape.py')
Invoke-PythonTest (Join-Path $PSScriptRoot '..\tests\test_configuration.py')
Invoke-PythonTest (Join-Path $PSScriptRoot '..\tests\test_host_services.py')
Invoke-PythonTest (Join-Path $PSScriptRoot '..\tests\test_awt_image_extraction.py')
Invoke-PythonTest (Join-Path $PSScriptRoot '..\tests\test_lcms_rgb16.py')
Invoke-PythonTest (Join-Path $PSScriptRoot '..\tests\test_tika_python_compat.py')
Invoke-PythonTest (Join-Path $PSScriptRoot '..\tests\test_tika_capabilities.py')
