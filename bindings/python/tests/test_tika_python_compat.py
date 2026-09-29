#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import sys

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

import tika_ape

from tika_ape import parser
from tika_ape import detector
from tika_ape import language


def main() -> None:
    fixture_path = PROJECT_ROOT / 'tests' / 'fixtures' / 'sample.txt'

    tika_ape.initVM()

    parsed_file = parser.from_file(fixture_path)
    parsed_buffer = parser.from_buffer('APEBind turns portable CLI applications into packages.')

    assert parsed_file['status'] == 200
    assert 'APEBind turns portable CLI applications' in parsed_file['content']
    assert parsed_file['metadata']['Content-Type'].startswith('text/plain')

    assert parsed_buffer['status'] == 200
    assert 'APEBind turns portable CLI applications' in parsed_buffer['content']
    assert detector.from_file(fixture_path).startswith('text/plain')
    assert language.from_buffer('This is just some text in English.') == 'eng'

    integration_source = os.environ.get('TIKA_APE_INTEGRATION_SOURCE')
    if integration_source is None:
        return

    parsed_pdf = parser.from_file(integration_source)

    assert 'Attention Is All You Need' in parsed_pdf['content']


if __name__ == '__main__':
    main()
