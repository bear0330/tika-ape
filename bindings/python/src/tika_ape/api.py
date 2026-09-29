#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""The handwritten, Python-native Tika API."""

from __future__ import annotations

from contextlib import contextmanager
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterator

from . import _generated
from .host_services import _TikaHostServices


_host_services_enabled = True
_host_services: _TikaHostServices | None = None
_inline_images_enabled = False
_inline_images_config = Path(__file__).with_name('config') / 'inline-images.json'


def configure(*, host_services: bool = True, inline_images: bool = False) -> None:
    """Configure the bundled Tika runtime before parsing documents."""
    global _host_services_enabled, _host_services, _inline_images_enabled

    if _host_services is not None and not host_services:
        _host_services.close()
        _host_services = None

    _host_services_enabled = host_services
    _inline_images_enabled = inline_images


def initVM() -> None:
    """Compatibility alias for tika-python; no JVM is initialized."""
    configure()


def _client() -> Any:
    global _host_services

    if not _host_services_enabled:
        return _generated._CLIENT

    if _host_services is None:
        _host_services = _TikaHostServices()
        _host_services.start()

    return _host_services


def _config_path(config: str | Path | None) -> str | Path | None:
    if config is not None:
        return config

    if _inline_images_enabled:
        return _inline_images_config

    return None


@contextmanager
def _source_path(source: str | Path) -> Iterator[str]:
    candidate = Path(source)
    if not candidate.exists():
        yield str(source)
        return

    working_directory = Path.cwd().resolve()
    source_path = candidate.resolve()

    try:
        relative_path = Path(os.path.relpath(source_path, working_directory))
    except ValueError:
        relative_path = Path('..')

    if not relative_path.parts or relative_path.parts[0] != '..':
        yield str(relative_path)
        return

    with tempfile.TemporaryDirectory(
        dir=working_directory,
        prefix='.tika-ape-',
    ) as temporary_directory:
        staged_path = Path(temporary_directory) / source_path.name
        shutil.copyfile(source_path, staged_path)

        yield os.path.relpath(staged_path, working_directory)


def _invoke(operation: str, source: Any, **options: Any) -> Any:
    with _source_path(source) as source_path:
        options['source'] = source_path
        options['config'] = _config_path(options.get('config'))

        return _client().invoke(operation, options)


def extract(source: Any, config: str | Path | None = None, **options: Any) -> str:
    return _invoke('extract', source, config=config, **options)


def extract_text(source: Any, config: str | Path | None = None, **options: Any) -> str:
    return _invoke('extract_text', source, config=config, **options)


def extract_xml(source: Any, config: str | Path | None = None, **options: Any) -> str:
    return _invoke('extract_xml', source, config=config, **options)


def extract_json(source: Any, config: str | Path | None = None, **options: Any) -> dict[str, Any]:
    return _invoke('extract_json', source, config=config, **options)


def metadata(source: Any, config: str | Path | None = None, **options: Any) -> str:
    return _invoke('metadata', source, config=config, **options)


def detect(source: Any, config: str | Path | None = None, **options: Any) -> str:
    return _invoke('detect', source, config=config, **options)


def detect_encoding(
    source: Any,
    config: str | Path | None = None,
    **options: Any,
) -> str | None:
    document = extract_json(source, config=config, **options)

    return document.get('Content-Encoding') or document.get('tk:detected-encoding')


def detect_language(
    source: Any,
    config: str | Path | None = None,
    **options: Any,
) -> str | None:
    return _invoke('detect_language', source, config=config, **options)
