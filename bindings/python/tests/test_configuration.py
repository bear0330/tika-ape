#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""Configuration selection regressions."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from tika_ape import api


def main() -> None:
    api.configure(ocr=False)

    assert api._config_path(None).name == 'inline-images-no-ocr.json'

    api.configure(inline_images=False, ocr=False)

    assert api._config_path(None).name == 'no-ocr.json'

    api.configure()

    assert api._config_path(None).name == 'inline-images.json'


if __name__ == '__main__':
    main()
