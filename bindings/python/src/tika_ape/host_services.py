#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - Python Host Services provider
# Copyright (C) 2025-2026 Tika APE contributors

"""Tika-specific alternate implementations for Java APE native methods."""

from __future__ import annotations

import json
import secrets
import struct
import threading

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from . import _generated
from ._runtime import APEClient


_AWT_INITIALIZERS = frozenset({
    'java.awt.Toolkit.initIDs()V',
    'java.awt.image.BufferedImage.initIDs()V',
    'java.awt.image.ColorModel.initIDs()V',
    'java.awt.image.IndexColorModel.initIDs()V',
    'java.awt.image.Raster.initIDs()V',
    'java.awt.image.SampleModel.initIDs()V',
    'java.awt.image.SinglePixelPackedSampleModel.initIDs()V',
    'sun.awt.image.ByteComponentRaster.initIDs()V',
    'sun.awt.image.BytePackedRaster.initIDs()V',
    'sun.awt.image.IntegerComponentRaster.initIDs()V',
    'sun.java2d.Disposer.initIDs()V',
})


class _HostEnabledAPEClient(APEClient):
    def __init__(self, environment: dict[str, str]) -> None:
        super().__init__(
            _generated._CLIENT._binary_path,
            _generated._OPERATIONS,
            _generated._RUNTIME,
        )
        self._host_environment = environment

    def _environment(self) -> dict[str, str]:
        environment = super()._environment()
        environment.update(self._host_environment)

        return environment


class _UnsupportedNativeMethod(Exception):
    pass


class _TikaHostService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    @staticmethod
    def _is_awt_initializer(service: str) -> bool:
        return service in _AWT_INITIALIZERS

    def invoke(self, service: str) -> dict[str, object]:
        self.calls.append(service)

        if self._is_awt_initializer(service):
            return {'type': 'void'}

        raise _UnsupportedNativeMethod(service)


class _HostServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, token: str) -> None:
        super().__init__(('127.0.0.1', 0), _HostRequestHandler)
        self.token = token
        self.service = _TikaHostService()


class _HostRequestHandler(BaseHTTPRequestHandler):
    server: _HostServer

    def log_message(self, _format: str, *_args: object) -> None:
        pass

    @staticmethod
    def _frame(header: dict[str, object]) -> bytes:
        encoded_header = json.dumps(header, separators=(',', ':')).encode('utf-8')

        return struct.pack('>I', len(encoded_header)) + encoded_header

    def _send(self, header: dict[str, object]) -> None:
        response = self._frame(header)

        self.send_response(200)
        self.send_header('Content-Type', 'application/vnd.java-ape-host; version=1')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self) -> None:
        if self.path != '/v1/invoke':
            self.send_error(404)
            return

        if self.headers.get('Authorization') != f'Bearer {self.server.token}':
            self._send({
                'ok': False,
                'error': {'type': 'unauthorized', 'message': 'invalid host token'},
            })
            return

        request = self.rfile.read(int(self.headers['Content-Length']))
        header_length = struct.unpack('>I', request[:4])[0]
        header = json.loads(request[4:4 + header_length])
        service = header['service']

        try:
            result = self.server.service.invoke(service)
        except _UnsupportedNativeMethod:
            self._send({
                'ok': False,
                'error': {
                    'type': 'unsupported',
                    'message': f'unsupported Tika host service: {service}',
                },
            })
            return

        self._send({'ok': True, 'return': result})


class _TikaHostServices:
    """Own the localhost provider used by the Python-native API."""

    def __init__(self) -> None:
        self._token = secrets.token_urlsafe(32)
        self._server = _HostServer(self._token)
        self._thread: threading.Thread | None = None
        self._client = _HostEnabledAPEClient({
            'JAVA_APE_HOST': f'http://127.0.0.1:{self._server.server_port}',
            'JAVA_APE_HOST_TOKEN': self._token,
            'JAVA_APE_VIRTUAL_LIBRARIES': 'awt,fontmanager',
        })

    def start(self) -> None:
        if self._thread is not None:
            return

        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name='tika-ape-host-services',
            daemon=True,
        )
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()

        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def invoke(self, operation: str, options: dict[str, Any]) -> Any:
        return self._client.invoke(operation, options)

    def raw(self, arguments: list[str]) -> Any:
        return self._client.raw(arguments)
