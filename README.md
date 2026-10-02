# tika-ape

Apache Tika 4 as a portable CLI and from Python or Node.js, without installing
Java.

`tika-ape` bundles Apache Tika 4 and its Java runtime into a portable
`tika.com`, then exposes document extraction through language-native bindings
generated with [APEBind](https://github.com/nuwainfo/apebind). No system Java,
Tika server, or JVM configuration is required.

<img width="724" height="543" alt="圖片" src="https://github.com/user-attachments/assets/02a25358-3c21-46cb-bc68-a75c187be8ae" />


## Use `tika.com`

You can download the latest [`tika.com` release](https://github.com/bear0330/tika-ape/releases)
with `tika-config.json` and use it directly as an APE CLI:

```sh
./tika.com --config=tika-config.json --text report.pdf
./tika.com --config=tika-config.json --json report.pdf
./tika.com --config=tika-config.json --detect report.pdf
```

The standalone CLI has no JNI support, so its companion text-only profile
disables PDF inline-image extraction. It still extracts text, emits document
metadata as JSON, and detects MIME types without a host Java runtime. The
Python binding supplies a Host Services provider for
[java-ape](https://github.com/bear0330/java-ape), and therefore enables the
tested inline-image path by default.

## Install a binding

Install the Python wheel directly from the release:

```sh
python -m pip install https://github.com/bear0330/tika-ape/releases/download/v0.2.7/tika_ape-0.2.7-py3-none-any.whl
```

Or install the Node.js package tarball:

```sh
npm install https://github.com/bear0330/tika-ape/releases/download/v0.2.7/tika-ape-0.2.7.tgz
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

Node.js exposes the same text-oriented CLI capability:

```js
import { extractJson, extractText } from 'tika-ape';

const text = await extractText('report.pdf');
const metadata = await extractJson('report.pdf');
```

Unlike standalone `tika.com`, the Python binding enables PDF inline-image
extraction by default because it bundles a Host Services provider. Node.js
does not yet ship that provider, so it remains text-oriented. Use Python's
text-only profile when embedded image output is unnecessary:

```python
import tika_ape

tika_ape.configure(inline_images=False)
text = tika_ape.extract_text('report.pdf')
```

The Python provider also implements LCMS profile and colour conversion through
Pillow's `ImageCms`. For PDFBox's tested image path, it registers a generic
`MaskBlit` primitive and handles unclipped, maskless `Src` and `SrcOver`
compositing through `BufferedImage` pixels. This covers the Klook voucher PDF
used by the regression suite.

`tika_ape.initVM()` remains as a `tika-python` compatibility alias; it
configures the package and does not start a JVM.

## Scope

Text, metadata, MIME detection, encoding, language detection, and normal PDF
extraction run without host Java. Full JNI/AWT compatibility is not promised.
The Python binding supports the tested PDFBox inline-image paths, including
Klook's ICC/masked-image document. Other composite rules, clipping, and
coverage-mask operations remain outside the current Host provider.
OCR and media-transcoding parsers still need their respective external tools.

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
