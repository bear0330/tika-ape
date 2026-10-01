# tika-ape Node.js

`tika-ape` is an ESM package built from the repository's portable Apache Tika
4 `tika.com`. It extracts text, metadata, MIME types, detected encodings, and
document languages without requiring a host Java installation.

## Install

Install the tarball published with a GitHub Release:

```sh
npm install https://github.com/bear0330/tika-ape/releases/download/v0.2.7/tika-ape-0.2.7.tgz
```

Replace the version in both places when selecting another release.

## Development

The APE and shared document fixtures are intentionally not committed in this
project. Prepare them from the repository root before testing or building:

```powershell
& .\scripts\test.ps1
& .\scripts\build.ps1
```

On Linux or macOS, use `./scripts/test.sh` and `./scripts/build.sh` instead.
The build script copies the root `tika.com` into `src/bin/`, so the npm package
remains self-contained. The root prepare script downloads `tika.com` from the
latest GitHub release when its local cache is absent.

## Use

```js
import {
  detect,
  detectEncoding,
  detectLanguage,
  extractJson,
  extractText,
} from 'tika-ape';

const text = await extractText('report.pdf');
const document = await extractJson('report.pdf');
const mimeType = await detect('report.pdf');
const encoding = await detectEncoding('report.pdf');
const language = await detectLanguage('report.pdf');
```

The Node binding uses Tika's text-oriented profile. PDF inline-image extraction
requires the Host Services image provider currently supplied by the Python
binding, and is not available in Node.js yet.

For migration from the legacy `tika` npm package, the package also offers
callback-compatible `extract()`, `text()`, `xhtml()`, `meta()`, `type()`,
`charset()`, `typeAndCharset()`, and `language()` helpers. They also return
promises. `language()` accepts text and returns no confidence value because
Tika CLI does not expose one. OCR and media transcoding remain explicit Tika
external-parser integrations and require the relevant external executable.

See the repository [README](../../README.md) for package architecture and
shared-fixture testing.
