# SPDX-License-Identifier: Apache-2.0

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$targetPath = Join-Path $repositoryRoot 'tika.com'
$version = $env:TIKA_APE_VERSION
$forceDownload = $env:TIKA_APE_FORCE_DOWNLOAD -eq '1'

if ((Test-Path -LiteralPath $targetPath) -and -not $forceDownload) {
    Write-Host "Using cached $targetPath"
    return
}

$releasePath = if ([string]::IsNullOrWhiteSpace($version)) {
    'latest'
} else {
    "download/$version"
}

$downloadUrl = if ($releasePath -eq 'latest') {
    'https://github.com/bear0330/tika-ape/releases/latest/download/tika.com'
} else {
    "https://github.com/bear0330/tika-ape/releases/download/$version/tika.com"
}

$temporaryPath = "$targetPath.download"
Write-Host "Downloading $downloadUrl"
Invoke-WebRequest -UseBasicParsing -Uri $downloadUrl -OutFile $temporaryPath

if ((Get-Item -LiteralPath $temporaryPath).Length -eq 0) {
    throw 'Downloaded tika.com is empty'
}

Move-Item -LiteralPath $temporaryPath -Destination $targetPath -Force
