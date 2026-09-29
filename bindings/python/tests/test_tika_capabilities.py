#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""Document capability regressions adapted from tika-python's parser tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / 'tests' / 'fixtures'
REMOTE_FIXTURE_URL = 'https://chrismattmann.github.io/tika-python/_static/test-files/remote.pdf'
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import tika_ape

from tika_ape import detector, parser, pdf


def main() -> None:
    pdf_path = FIXTURES / 'rwservlet.pdf'
    html_path = FIXTURES / 'remote.html'
    jpg_path = FIXTURES / 'remote.jpg'
    mp3_path = FIXTURES / 'remote.mp3'

    tika_ape.initVM()

    pdf_result = parser.from_file(pdf_path)
    html_result = parser.from_file(html_path)
    jpg_result = parser.from_file(jpg_path)
    mp3_result = parser.from_file(mp3_path)
    remote_fixture_enabled = os.environ.get('TIKA_APE_TEST_REMOTE') == '1'

    assert pdf_result['metadata']['Content-Type'] == 'application/pdf'
    assert pdf_result['content']
    assert html_result['metadata']['Content-Type'].startswith('text/html')
    assert 'Tika Python Remote HTML Fixture' in html_result['content']
    assert jpg_result['status'] == 200
    assert mp3_result['status'] == 200

    assert tika_ape.detect_encoding(FIXTURES / 'sample.txt') == 'windows-1252'
    assert tika_ape.detect_language(html_path) == 'eng'

    if remote_fixture_enabled:
        remote_pdf_result = parser.from_file(REMOTE_FIXTURE_URL)

        assert remote_pdf_result['metadata']['Content-Type'] == 'application/pdf'

    with pdf_path.open('rb') as file_object:
        binary_result = parser.from_file(file_object)

    assert binary_result['metadata']['Content-Type'] == 'application/pdf'
    assert detector.from_file(pdf_path) == 'application/pdf'
    assert detector.from_buffer('Good evening, David. How are you?').startswith('text/plain')
    assert pdf.text_from_pdf_pages(pdf_path)


if __name__ == '__main__':
    main()
