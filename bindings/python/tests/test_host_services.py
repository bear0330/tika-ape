#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - Host Services tests
# Copyright (C) 2025-2026 Tika APE contributors

"""Exercise Tika's Java2D host capability without a Java subprocess."""

from __future__ import annotations

import sys
import time

from pathlib import Path

from PIL import ImageCms


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from tika_ape.host_services import _HostServer, _TikaHostService


def _integer(value: int) -> dict[str, object]:
    return {'type': 'int', 'value': value}


def _profile_bytes() -> dict[str, str]:
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))

    return _TikaHostService._encode_bytes(profile.tobytes())


def _request(
    owner: str,
    name: str,
    descriptor: str,
    arguments: list[dict[str, object]],
) -> dict[str, object]:
    return {
        'owner': owner,
        'name': name,
        'descriptor': descriptor,
        'arguments': arguments,
    }


def _create_transform(
    service: _TikaHostService,
    source_profile: int,
    destination_profile: int,
    input_format: int,
    output_format: int,
    reference: int,
) -> int:
    response = service.replace_native_method(_request(
        'sun/java2d/cmm/lcms/LCMS',
        'createNativeTransform',
        '([JIIILjava/lang/Object;)J',
        [
            {
                'type': 'long[]',
                'value': [source_profile, destination_profile],
            },
            _integer(0),
            _integer(input_format),
            _integer(output_format),
            {'type': 'java-ref', 'id': reference},
        ],
    ))

    return response['return']['value']


def _convert_pixel(
    service: _TikaHostService,
    transform: int,
    source: dict[str, object],
    destination: dict[str, object],
    source_stride: int,
    destination_stride: int,
    source_type: int,
    destination_type: int,
) -> dict[str, object]:
    response = service.replace_native_method(_request(
        'sun/java2d/cmm/lcms/LCMS',
        'colorConvert',
        '(JIIIIIILjava/lang/Object;Ljava/lang/Object;II)V',
        [
            {'type': 'long', 'value': transform},
            _integer(1),
            _integer(1),
            _integer(0),
            _integer(source_stride),
            _integer(0),
            _integer(destination_stride),
            source,
            destination,
            _integer(source_type),
            _integer(destination_type),
        ],
    ))

    assert response['return'] == {'type': 'void'}

    return response['mutations'][0]['value']


def main() -> None:
    service = _TikaHostService()
    initialized = service.replace_native_method(_request(
        'java/awt/image/ColorModel',
        'initIDs',
        '()V',
        [],
    ))
    source_profile = service.replace_native_method(_request(
        'sun/java2d/cmm/lcms/LCMS',
        'loadProfileNative',
        '([BLjava/lang/Object;)J',
        [_profile_bytes(), {'type': 'java-ref', 'id': 1}],
    ))
    destination_profile = service.replace_native_method(_request(
        'sun/java2d/cmm/lcms/LCMS',
        'loadProfileNative',
        '([BLjava/lang/Object;)J',
        [_profile_bytes(), {'type': 'java-ref', 'id': 2}],
    ))
    assert initialized == {'return': {'type': 'void'}}
    source_profile_handle = source_profile['return']['value']
    destination_profile_handle = destination_profile['return']['value']

    bgr_transform = _create_transform(
        service,
        source_profile_handle,
        destination_profile_handle,
        0x00000419,
        0x00000419,
        3,
    )
    assert _convert_pixel(
        service,
        bgr_transform,
        _TikaHostService._encode_bytes(b'\x03\x02\x01'),
        _TikaHostService._encode_bytes(b'\x00\x00\x00'),
        3,
        3,
        0,
        0,
    ) == _TikaHostService._encode_bytes(b'\x03\x02\x01')

    component_transform = _create_transform(
        service,
        source_profile_handle,
        destination_profile_handle,
        0x00000019,
        0x00000419,
        4,
    )
    assert _convert_pixel(
        service,
        component_transform,
        _TikaHostService._encode_bytes(b'\x01\x02\x03'),
        _TikaHostService._encode_bytes(b'\x00\x00\x00'),
        3,
        3,
        0,
        0,
    ) == _TikaHostService._encode_bytes(b'\x03\x02\x01')

    bgra_transform = _create_transform(
        service,
        source_profile_handle,
        destination_profile_handle,
        0x00004499,
        0x00004499,
        5,
    )
    assert _convert_pixel(
        service,
        bgra_transform,
        _TikaHostService._encode_bytes(b'\x03\x02\x01\x04'),
        _TikaHostService._encode_bytes(b'\x00\x00\x00\x00'),
        4,
        4,
        0,
        0,
    ) == _TikaHostService._encode_bytes(b'\x03\x02\x01\x04')

    assert _convert_pixel(
        service,
        bgra_transform,
        {'type': 'int[]', 'value': [0x04010203]},
        {'type': 'int[]', 'value': [0]},
        4,
        4,
        2,
        2,
    ) == {'type': 'int[]', 'value': [0x04010203]}

    rgb16_transform = _create_transform(
        service,
        source_profile_handle,
        destination_profile_handle,
        0x0000001A,
        0x00000419,
        6,
    )
    assert _convert_pixel(
        service,
        rgb16_transform,
        {'type': 'short[]', 'value': [-1, -32768, 0]},
        _TikaHostService._encode_bytes(b'\x00\x00\x00'),
        6,
        3,
        1,
        0,
    ) == _TikaHostService._encode_bytes(b'\x00\x80\xff')

    rgb16_destination_transform = _create_transform(
        service,
        source_profile_handle,
        destination_profile_handle,
        0x00000419,
        0x0000001A,
        7,
    )
    assert _convert_pixel(
        service,
        rgb16_destination_transform,
        _TikaHostService._encode_bytes(b'\x03\x02\x01'),
        {'type': 'short[]', 'value': [0, 0, 0]},
        3,
        6,
        0,
        1,
    ) == {'type': 'short[]', 'value': [257, 514, 771]}

    assert service._composite_pixels(
        [0x80ff0000],
        [0xff0000ff],
        service._ALPHA_COMPOSITE_SRC_OVER,
        1.0,
    ) == [0xff80007f]
    assert service._composite_pixels(
        [0x80ff0000],
        [0xff0000ff],
        service._ALPHA_COMPOSITE_SRC,
        1.0,
    ) == [0x80ff0000]

    server = _HostServer('test-token')
    server.start()

    time.sleep(0.3)
    server.close()


if __name__ == '__main__':
    main()
