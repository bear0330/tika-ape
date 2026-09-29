#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - Host Services tests
# Copyright (C) 2025-2026 Tika APE contributors

from __future__ import annotations

import json
import struct
import sys

from http.client import HTTPConnection
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from tika_ape.host_services import _TikaHostServices


def encode_request(service: str) -> bytes:
    header = json.dumps({
        'version': 1,
        'service': service,
        'arguments': [],
    }, separators=(',', ':')).encode('utf-8')

    return struct.pack('>I', len(header)) + header


def send_request(client: _TikaHostServices, service: str) -> dict[str, object]:
    connection = HTTPConnection('127.0.0.1', client._server.server_port)
    connection.request('POST', '/v1/invoke', encode_request(service), {
        'Authorization': f'Bearer {client._token}',
        'Content-Type': 'application/vnd.java-ape-host; version=1',
    })
    response = connection.getresponse()
    payload = response.read()
    header_length = struct.unpack('>I', payload[:4])[0]
    header = json.loads(payload[4:4 + header_length])

    assert response.status == 200

    return header


def main() -> None:
    client = _TikaHostServices()
    client.start()

    try:
        initialized = send_request(client, 'java.awt.image.ColorModel.initIDs()V')
        unsupported = send_request(client, 'java.awt.image.ColorModel.getRGB(I)I')
    finally:
        client.close()

    assert initialized == {'ok': True, 'return': {'type': 'void'}}
    assert unsupported == {
        'ok': False,
        'error': {
            'type': 'unsupported',
            'message': 'unsupported Tika host service: java.awt.image.ColorModel.getRGB(I)I',
        },
    }

if __name__ == '__main__':
    main()
