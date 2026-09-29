#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - Document Digest example
# Copyright (C) 2025-2026 Tika APE contributors

"""Turn mixed documents into one Markdown corpus for an LLM or RAG pipeline."""

from __future__ import annotations

import argparse
import json

from pathlib import Path

import tika_ape


def collect_documents(paths: list[Path]) -> list[Path]:
    documents: list[Path] = []

    for path in paths:
        if path.is_file():
            documents.append(path)
            continue

        documents.extend(candidate for candidate in path.rglob('*') if candidate.is_file())

    return sorted(documents)


def render_document(
    path: Path,
    media_type: str,
    metadata: dict[str, object],
    text: str,
) -> str:
    rendered_metadata = json.dumps(metadata, ensure_ascii=False, indent=2)

    return '\n'.join([
        f'## {path.name}',
        '',
        f'- Source: `{path}`',
        f'- Detected type: `{media_type}`',
        '',
        '### Metadata',
        '',
        '```json',
        rendered_metadata,
        '```',
        '',
        '### Extracted text',
        '',
        text.strip(),
        '',
    ])


def build_digest(paths: list[Path], output_path: Path) -> None:
    documents = collect_documents(paths)
    sections = ['# Document Digest', '']

    for path in documents:
        media_type = tika_ape.detect(path)
        metadata = tika_ape.extract_json(path)
        text = tika_ape.extract_text(path)
        sections.append(render_document(path, media_type, metadata, text))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(sections), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, default=Path('document-digest.md'))
    options = parser.parse_args()

    build_digest(options.paths, options.output)

    print(f'Wrote {options.output}')


if __name__ == '__main__':
    main()
