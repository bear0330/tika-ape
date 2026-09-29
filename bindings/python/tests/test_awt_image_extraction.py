#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - AWT image extraction regression test
# Copyright (C) 2025-2026 Tika APE contributors

"""Verify real PDF image extraction through the bundled Host Services provider."""

from __future__ import annotations

import sys

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / 'tests' / 'fixtures'
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import tika_ape

from tika_ape import APEProcessError
from tika_ape import api
from tika_ape.host_services import _AWT_INITIALIZERS


def main() -> None:
    source = FIXTURES / 'tika-inline-images.pdf'
    image_report = FIXTURES / 'rwservlet.pdf'

    tika_ape.configure(host_services=False, inline_images=True)

    try:
        tika_ape.extract_xml(source)
    except APEProcessError as error:
        assert 'ColorModel' in error.result.stderr
        assert 'no awt in system library path' in error.result.stderr
    else:
        raise AssertionError('image extraction unexpectedly worked without Host Services')

    tika_ape.configure(host_services=True, inline_images=True)
    extracted = tika_ape.extract_xml(source)

    assert extracted.count('embedded:image-') == 2
    assert 'embedded:image-0.jpg' in extracted
    assert 'embedded:image-1.tif' in extracted

    report = tika_ape.extract_xml(image_report)

    assert 'Allegheny County Health Department' in report

    host_services = api._host_services
    assert host_services is not None
    invoked = set(host_services._server.service.calls)

    assert invoked <= _AWT_INITIALIZERS
    assert {
        'java.awt.image.BufferedImage.initIDs()V',
        'java.awt.image.ColorModel.initIDs()V',
        'java.awt.image.Raster.initIDs()V',
        'sun.java2d.Disposer.initIDs()V',
    } <= invoked


if __name__ == '__main__':
    main()
