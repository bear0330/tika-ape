#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""PDF conveniences compatible with tika-python's page text helper."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from . import api


def text_from_pdf_pages(filename: str | Path) -> list[str]:
    document = ElementTree.fromstring(api.extract_xml(filename))
    pages: list[str] = []

    for element in document.iter():
        tag = element.tag.rsplit('}', maxsplit=1)[-1]
        classes = element.attrib.get('class', '').split()

        if tag != 'div' or 'page' not in classes:
            continue

        text = ' '.join(''.join(element.itertext()).split())
        pages.append(text)

    return pages
