#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""A tika-python-compatible MIME detection surface."""

from __future__ import annotations

import tempfile

from pathlib import Path
from typing import BinaryIO

from . import api


def from_file(filename: str | Path | BinaryIO) -> str:
    if hasattr(filename, 'read'):
        return from_buffer(filename.read())

    return api.detect(filename)


def from_buffer(value: str | bytes) -> str:
    content = value.encode('utf-8') if isinstance(value, str) else value

    with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
        temporary_file.write(content)
        temporary_path = Path(temporary_file.name)

    try:
        return api.detect(temporary_path)
    finally:
        temporary_path.unlink()
