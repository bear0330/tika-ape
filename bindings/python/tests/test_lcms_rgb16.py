#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - LCMS RGB16 regression test
# Copyright (C) 2025-2026 Tika APE contributors

"""Verify 16-bit ICC PDF images use the Java APE LCMS Host Service."""

from __future__ import annotations

import sys
import tempfile

from pathlib import Path

from PIL import ImageCms


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import tika_ape


def _write_icc_pdf(path: Path) -> None:
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    color_pixels = bytes([
        0xFF, 0xFF,
        0x80, 0x00,
        0x00, 0x00,
    ])
    content = b'q 1 0 0 1 0 0 cm /Image0 Do Q\n'
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        (
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1 1] '
            b'/Resources << /XObject << /Image0 4 0 R >> >> /Contents 6 0 R >>'
        ),
        (
            b'<< /Type /XObject /Subtype /Image /Width 1 /Height 1 '
            b'/ColorSpace [/ICCBased 5 0 R] /BitsPerComponent 16 '
            b'/Length ' + str(len(color_pixels)).encode('ascii') + b' >>\nstream\n'
            + color_pixels + b'\nendstream'
        ),
        b'<< /N 3 /Length ' + str(len(profile)).encode('ascii') + b' >>\nstream\n'
        + profile + b'\nendstream',
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
    with tempfile.TemporaryDirectory() as temporary_directory:
        source = Path(temporary_directory) / 'icc-rgb16.pdf'
        _write_icc_pdf(source)

        document = tika_ape.extract_xml(source)

    assert 'embedded:image-0.png' in document


if __name__ == '__main__':
    main()
