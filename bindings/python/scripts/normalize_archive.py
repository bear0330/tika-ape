#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - Python release archive normalizer
# Copyright (C) 2025-2026 Tika APE contributors

"""Set the bundled APE executable mode in built Python archives."""

from __future__ import annotations

import sys
import tarfile
import zipfile

from pathlib import Path


_APE_SUFFIX = 'tika_ape/bin/tika.com'
_EXECUTABLE_MODE = 0o100755


def _is_ape(name: str) -> bool:
    return name.endswith(_APE_SUFFIX)


def _normalize_tarball(archive_path: Path) -> None:
    temporary_path = archive_path.with_suffix('.tmp')

    with tarfile.open(archive_path, 'r:gz') as source:
        with tarfile.open(temporary_path, 'w:gz') as destination:
            for member in source.getmembers():
                if _is_ape(member.name):
                    member.mode = 0o755

                data = source.extractfile(member) if member.isfile() else None
                destination.addfile(member, data)

    temporary_path.replace(archive_path)


def _normalize_wheel(archive_path: Path) -> None:
    temporary_path = archive_path.with_suffix('.tmp')

    with zipfile.ZipFile(archive_path) as source:
        with zipfile.ZipFile(temporary_path, 'w') as destination:
            for member in source.infolist():
                if _is_ape(member.filename):
                    member.create_system = 3
                    member.external_attr = _EXECUTABLE_MODE << 16

                destination.writestr(member, source.read(member.filename))

    temporary_path.replace(archive_path)


def main() -> None:
    for argument in sys.argv[1:]:
        archive_path = Path(argument)

        if archive_path.name.endswith('.tar.gz'):
            _normalize_tarball(archive_path)
            continue

        if archive_path.suffix == '.whl':
            _normalize_wheel(archive_path)
            continue

        raise ValueError(f'unsupported release archive: {archive_path}')


if __name__ == '__main__':
    main()
