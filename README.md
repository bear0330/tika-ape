# tika-ape

Apache Tika 4 from Python and Node.js, without installing Java.

`tika-ape` bundles Apache Tika 4 and its Java runtime into a portable
`tika.com`, then exposes document extraction through language-native bindings
generated with [APEBind](https://github.com/nuwainfo/apebind). No system Java,
Tika server, or JVM configuration is required.

`tika.com` is a release artifact rather than a Git object because it exceeds
GitHub's 100 MB file limit. Download it from the latest release:

```powershell
Invoke-WebRequest https://github.com/bear0330/tika-ape/releases/latest/download/tika.com -OutFile tika.com
```

```sh
curl -fL https://github.com/bear0330/tika-ape/releases/latest/download/tika.com -o tika.com
chmod +x tika.com
```

The Python wheel and Node.js tarball are release assets for the same reason.
They bundle `tika.com`; installing either package does not download or require
a host Java runtime.

## Install a binding

Install the Python wheel directly from the release:

```sh
python -m pip install https://github.com/bear0330/tika-ape/releases/download/v0.1.0/tika_ape-0.1.0-py3-none-any.whl
```

Or install the Node.js package tarball:

```sh
npm install https://github.com/bear0330/tika-ape/releases/download/v0.1.0/tika-ape-0.1.0.tgz
```

Replace both version strings with the chosen release version. The package
contains the same portable `tika.com` asset as the release.

## Bindings

Python provides a small, `tika-python`-compatible surface:

```python
import tika_ape
from tika_ape import parser

text = tika_ape.extract_text('report.pdf')
document = parser.from_file('report.pdf')
```

Node.js exposes the same underlying CLI capability:

```js
import { extractJson, extractText } from 'tika-ape';

const text = await extractText('report.pdf');
const metadata = await extractJson('report.pdf');
```

The Python package enables its bundled Host Services provider by default. This
allows PDFBox to decode and extract PDF image resources without a host AWT JNI
library. Tika's normal conservative PDF behavior remains the default. Enable
inline-image extraction when needed:

```python
import tika_ape

tika_ape.configure(inline_images=True)
xml = tika_ape.extract_xml('report.pdf')
```

Node.js provides the same opt-in behavior and runs its bundled Host Services
provider without a native Node addon:

```js
import { configure, extractXml } from 'tika-ape';

configure({ inlineImages: true });
const xml = await extractXml('report.pdf');
```

`tika_ape.initVM()` remains as a `tika-python` compatibility alias; it
configures the package and does not start a JVM.

## Scope

Text, metadata, MIME detection, encoding, language detection, and normal PDF
extraction run without host Java. Full JNI/AWT compatibility is not promised.
PDF inline-image extraction is opt-in and uses the bundled Host Services
provider for the specific Java native initializers required by this Tika path;
it is not general AWT emulation. OCR and media-transcoding parsers still need
their respective external tools.

## Examples

[`document_digest`](examples/document_digest/) is a small Python program that
turns a folder of mixed documents into one Markdown corpus with source paths,
MIME types, metadata, and extracted text. It is useful as an LLM-context or
RAG-ingestion step.

[`evidence_copilot`](examples/evidence_copilot/) is an optional local AI demo.
It downloads public AI materials, uses Tika to extract them, and uses a local
embedding model to create an evidence-backed HTML briefing. It requires
`sentence-transformers` and downloads its model on first use.

## Build the portable Tika executable

`tika.com` is built with [javacosmofy](https://github.com/bear0330/javacosmofy)
from the paired `java.com` and `java-modules.zip` assets released by
[java-ape](https://github.com/bear0330/java-ape). Tika needs the
`java.desktop` module closure.

The reviewed [tika.apebind.yaml](tika.apebind.yaml) is the generated binding
contract. Regenerate with [APEBind](https://github.com/nuwainfo/apebind):

```sh
apebind validate tika.apebind.yaml
apebind generate tika.apebind.yaml --ape tika.com --lang python -o bindings/python
apebind generate tika.apebind.yaml --ape tika.com --lang node -o bindings/node
```

## Test and package

Root tests use Python's standard library to verify the `tika.com` CLI itself.
Their fixtures are shared by every binding. `prepare` downloads the latest
release asset when the local cache is absent; set `TIKA_APE_VERSION` to pin a
tag or `TIKA_APE_FORCE_DOWNLOAD=1` to refresh it. Each binding owns its
language API tests and materializes the root APE and shared fixtures into
ignored local staging paths before testing or packaging:

```powershell
& .\scripts\test.ps1
& .\bindings\python\scripts\test.ps1
& .\bindings\node\scripts\test.ps1
```

On Linux or macOS, run `./scripts/test.sh`, `./bindings/python/scripts/test.sh`,
and `./bindings/node/scripts/test.sh`. Use the corresponding binding `build`
scripts to produce the Python wheel or npm tarball.

All fixtures live in `tests/fixtures/`. Each binding preparation script copies
that directory into its ignored `tests/fixtures/` staging path before tests run.
`TIKA_PYTHON_NOTICE` records the source and license for fixtures adapted from
`tika-python`.
