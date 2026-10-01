#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - AWT image extraction regression test
# Copyright (C) 2025-2026 Tika APE contributors

"""Verify PDF image extraction through the bundled Host Services provider."""

from __future__ import annotations

import sys
import tempfile
import zlib

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / 'tests' / 'fixtures'
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import tika_ape

from tika_ape import APEProcessError


def _write_masked_pdf(path: Path) -> None:
    color_pixels = zlib.compress(bytes([
        255, 0, 0,
        0, 255, 0,
        0, 0, 255,
        255, 255, 255,
    ]))
    alpha_pixels = zlib.compress(bytes([255, 128, 64, 0]))
    content = b'q 2 0 0 2 0 0 cm /Image0 Do Q\n'
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        (
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 2 2] '
            b'/Resources << /XObject << /Image0 4 0 R >> >> /Contents 6 0 R >>'
        ),
        (
            b'<< /Type /XObject /Subtype /Image /Width 2 /Height 2 '
            b'/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode '
            b'/SMask 5 0 R /Length ' + str(len(color_pixels)).encode('ascii') + b' >>\nstream\n'
            + color_pixels + b'\nendstream'
        ),
        (
            b'<< /Type /XObject /Subtype /Image /Width 2 /Height 2 '
            b'/ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode '
            b'/Length ' + str(len(alpha_pixels)).encode('ascii') + b' >>\nstream\n'
            + alpha_pixels + b'\nendstream'
        ),
        b'<< /Length ' + str(len(content)).encode('ascii') + b' >>\nstream\n' + content + b'endstream',
    ]
    document = bytearray(b'%PDF-1.4\n')
    offsets = [0]

    for number, body in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f'{number} 0 obj\n'.encode('ascii'))
        document.extend(body)
        document.extend(b'\nendobj\n')

    xref_offset = len(document)
    document.extend(f'xref\n0 {len(objects) + 1}\n'.encode('ascii'))
    document.extend(b'0000000000 65535 f \n')

    for offset in offsets[1:]:
        document.extend(f'{offset:010d} 00000 n \n'.encode('ascii'))

    document.extend(
        b'trailer\n<< /Size ' + str(len(objects) + 1).encode('ascii')
        + b' /Root 1 0 R >>\nstartxref\n'
        + str(xref_offset).encode('ascii') + b'\n%%EOF\n'
    )
    path.write_bytes(document)


def main() -> None:
    source = FIXTURES / 'tika-inline-images.pdf'

    extracted = tika_ape.extract_xml(source)

    assert extracted.count('embedded:image-') == 2
    assert 'embedded:image-0.jpg' in extracted
    assert 'embedded:image-1.tif' in extracted

    with tempfile.TemporaryDirectory() as temporary_directory:
        masked_pdf = Path(temporary_directory) / 'masked.pdf'
        _write_masked_pdf(masked_pdf)

        masked = tika_ape.extract_xml(masked_pdf)

    assert 'embedded:image-0.png' in masked

    tika_ape.configure(host_services=False, inline_images=False)
    text_only = tika_ape.extract_xml(source)

    assert 'embedded:image-' not in text_only

    tika_ape.configure(host_services=False, inline_images=True)

    try:
        tika_ape.extract_xml(source)
    except APEProcessError as error:
        assert 'ColorModel' in error.result.stderr
        assert 'no awt in system library path' in error.result.stderr
    else:
        raise AssertionError('image extraction unexpectedly worked without Host Services')


if __name__ == '__main__':
    main()
