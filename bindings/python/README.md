# tika-ape Python

`tika_ape` is a Python package built from the repository's portable Apache
Tika 4 `tika.com`. It extracts text, metadata, and MIME types without requiring
a host Java installation.

## Install

Install the wheel published with a GitHub Release:

```sh
python -m pip install https://github.com/bear0330/tika-ape/releases/download/v0.1.0/tika_ape-0.1.0-py3-none-any.whl
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

The bundled Host Services provider is enabled by default. To have Tika extract
PDF inline images as embedded resources, opt in to the upstream Tika setting:

```python
tika_ape.configure(inline_images=True)
xml = tika_ape.extract_xml('report.pdf')
```

The package also offers `tika-python`-style `parser`, `detector`, `language`,
and `pdf` modules. See the repository [README](../../README.md) for the
compatibility surface and examples.
