#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""A tika-python-compatible parser surface backed by bundled tika.com."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, BinaryIO

from . import api


def from_file(
    filename: str | Path | BinaryIO,
    serverEndpoint: object = None,
    service: str = 'all',
    xmlContent: bool = False,
    headers: object = None,
    config_path: str | Path | None = None,
    requestOptions: object = None,
    raw_response: bool = False,
) -> dict[str, Any] | tuple[int, str]:
    del serverEndpoint, headers, requestOptions

    if hasattr(filename, 'read'):
        file_name = getattr(filename, 'name', '')
        suffix = Path(str(file_name)).suffix

        return _from_buffer(
            filename.read(),
            service=service,
            config_path=config_path,
            suffix=suffix,
        )

    if xmlContent:
        raise NotImplementedError('XML output is not in the tika-ape schema')

    text = api.extract_text(filename, config=config_path)
    metadata = api.extract_json(filename, config=config_path)
    parsed = {
        'status': 200,
        'metadata': metadata if service != 'text' else None,
        'content': text if service != 'meta' else None,
    }

    if raw_response:
        return 200, json.dumps(parsed)

    return parsed


def from_buffer(
    value: str | bytes,
    serverEndpoint: object = None,
    xmlContent: bool = False,
    headers: object = None,
    config_path: str | Path | None = None,
    requestOptions: object = None,
    raw_response: bool = False,
    service: str = 'all',
) -> dict[str, Any] | tuple[int, str]:
    del serverEndpoint, headers, requestOptions

    return _from_buffer(
        value,
        xmlContent=xmlContent,
        config_path=config_path,
        raw_response=raw_response,
        service=service,
    )


def _from_buffer(
    value: str | bytes,
    *,
    xmlContent: bool = False,
    config_path: str | Path | None = None,
    raw_response: bool = False,
    service: str = 'all',
    suffix: str = '',
) -> dict[str, Any] | tuple[int, str]:
    content = value.encode('utf-8') if isinstance(value, str) else value

    with tempfile.NamedTemporaryFile(
        dir=Path.cwd(),
        suffix=suffix,
        delete=False,
    ) as temporary_file:
        temporary_file.write(content)
        temporary_path = Path(temporary_file.name)

    try:
        return from_file(
            temporary_path,
            service=service,
            xmlContent=xmlContent,
            config_path=config_path,
            raw_response=raw_response,
        )
    finally:
        temporary_path.unlink()
