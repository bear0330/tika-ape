# tika-ape Python

`tika_ape` is a Python package built from the repository's portable Apache
Tika 4 `tika.com`. It extracts text, metadata, and MIME types without requiring
a host Java installation.

## Install

Install the wheel published with a GitHub Release:

```sh
python -m pip install https://github.com/bear0330/tika-ape/releases/download/v0.2.7/tika_ape-0.2.7-py3-none-any.whl
```

Replace the version in both places when selecting another release.

## Development

The package staging copy of the APE and shared document fixtures is ignored.
Prepare it from the repository root before testing or building:

```powershell
& .\scripts\test.ps1
& .\scripts\build.ps1
```

On Linux or macOS, use `./scripts/test.sh` and `./scripts/build.sh` instead.
Both build scripts copy the root `tika.com` into `src/tika_ape/bin/`, so the
wheel remains self-contained. The root prepare script downloads `tika.com`
from the latest GitHub release when its local cache is absent.

## Use

```python
import tika_ape

text = tika_ape.extract_text('report.pdf')
document = tika_ape.extract_json('report.pdf')
encoding = tika_ape.detect_encoding('report.txt')
language = tika_ape.detect_language('report.html')
```

PDF inline-image extraction is enabled by default. Use the text-only profile
when embedded image output is not needed:

```python
tika_ape.configure(inline_images=False)
text = tika_ape.extract_text('report.pdf')
```

Tika runs external Tesseract OCR when it is installed. Disable it explicitly
when a portable, no-external-tool parse is required:

```python
tika_ape.configure(ocr=False)
text = tika_ape.extract_text('report.pdf')
```

Host Services is experimental. The Python provider supplies the exact AWT
initializers used by the tested PDFBox paths, LCMS colour conversion through
Pillow's `ImageCms`, and a generic `MaskBlit` primitive for unclipped,
maskless `Src` and `SrcOver` compositing. This covers the Klook voucher PDF in
the regression suite. It is not general Java2D emulation: other composite
rules, clipping, and coverage masks are not supported yet.

The package also offers `tika-python`-style `parser`, `detector`, `language`,
and `pdf` modules. See the repository [README](../../README.md) for the
compatibility surface and examples.
