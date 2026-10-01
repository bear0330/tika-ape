#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Tika APE - Python Host Services provider
# Copyright (C) 2025-2026 Tika APE contributors

"""Tika-specific alternate implementations for Java APE native methods."""

from __future__ import annotations

import base64
import os
import socket
import threading

from io import BytesIO
from typing import Any, Callable

from PIL import Image, ImageCms
from pylsp_jsonrpc.endpoint import Endpoint
from pylsp_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter

from . import _generated
from ._runtime import APEClient


_PixelLayout = tuple[str, str, int, int]
_AWT_INITIALIZERS = frozenset({
    'java/awt/Font.initIDs()V',
    'java/awt/Toolkit.initIDs()V',
    'java/awt/image/BufferedImage.initIDs()V',
    'java/awt/image/ColorModel.initIDs()V',
    'java/awt/image/IndexColorModel.initIDs()V',
    'java/awt/image/Raster.initIDs()V',
    'java/awt/image/SampleModel.initIDs()V',
    'java/awt/image/SinglePixelPackedSampleModel.initIDs()V',
    'sun/awt/image/ByteComponentRaster.initIDs()V',
    'sun/awt/image/BytePackedRaster.initIDs()V',
    'sun/awt/image/BufImgSurfaceData.initIDs(Ljava/lang/Class;Ljava/lang/Class;)V',
    'sun/awt/image/IntegerComponentRaster.initIDs()V',
    'sun/java2d/Disposer.initIDs()V',
    'sun/java2d/SurfaceData.initIDs()V',
    'sun/java2d/loops/GraphicsPrimitiveMgr.initIDs(Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;Ljava/lang/Class;)V',
    'sun/java2d/pipe/SpanClipRenderer.initIDs(Ljava/lang/Class;Ljava/lang/Class;)V',
    'sun/java2d/pipe/Region.initIDs()V',
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


class _TikaHostService:
    """Implement the narrow Java2D native surface required by Tika/PDFBox."""

    _LOAD_PROFILE = 'sun/java2d/cmm/lcms/LCMS.loadProfileNative([BLjava/lang/Object;)J'
    _GET_PROFILE_DATA = 'sun/java2d/cmm/lcms/LCMS.getProfileDataNative(J)[B'
    _GET_TAG = 'sun/java2d/cmm/lcms/LCMS.getTagNative(JI)[B'
    _CREATE_TRANSFORM = (
        'sun/java2d/cmm/lcms/LCMS.createNativeTransform([JIIILjava/lang/Object;)J'
    )
    _COLOR_CONVERT = (
        'sun/java2d/cmm/lcms/LCMS.colorConvert(JIIIIIILjava/lang/Object;'
        'Ljava/lang/Object;II)V'
    )
    _REGISTER_NATIVE_LOOPS = (
        'sun/java2d/loops/GraphicsPrimitiveMgr.registerNativeLoops()V'
    )
    _INITIALIZE_RASTER = (
        'sun/awt/image/BufImgSurfaceData.initRaster('
        'Ljava/lang/Object;IIIIIILjava/awt/image/IndexColorModel;)V'
    )
    _MASK_BLIT = (
        'sun/java2d/loops/MaskBlit.MaskBlit('
        'Lsun/java2d/SurfaceData;Lsun/java2d/SurfaceData;'
        'Ljava/awt/Composite;Lsun/java2d/pipe/Region;'
        'IIIIII[BII)V'
    )
    _ALPHA_COMPOSITE_SRC = 2
    _ALPHA_COMPOSITE_SRC_OVER = 3
    _BYTE_BUFFER_TYPE = 0
    _SHORT_BUFFER_TYPE = 1
    _INT_BUFFER_TYPE = 2
    _FORMATTER_BYTES_MASK = 0x7
    _FORMATTER_CHANNELS_SHIFT = 3
    _FORMATTER_EXTRA_SHIFT = 7
    _FORMATTER_SWAP = 0x400
    _FORMATTER_SWAP_FIRST = 0x4000
    _FORMATTER_COLOR_SPACE_SHIFT = 16
    _GRAY_COLOR_SPACE = 3
    _RGB_COLOR_SPACE = 4
    _ICC_HEADER_SIZE = 128
    _ICC_TAG_TABLE_OFFSET = 128
    _ICC_TAG_ENTRY_SIZE = 12
    _ICC_HEADER_TAG = int.from_bytes(b'head', 'big')

    def __init__(self) -> None:
        self.calls: list[str] = []
        self._execute_environment: Callable[[int, list[dict[str, object]]], dict[str, object]] | None = None
        self._next_handle = 1
        self._profiles: dict[int, tuple[bytes, ImageCms.ImageCmsProfile]] = {}
        self._transforms: dict[int, tuple[Any, _PixelLayout, _PixelLayout]] = {}

    def replace_native_method(self, parameters: dict[str, Any]) -> dict[str, object]:
        identity = self._identity(parameters)
        self.calls.append(identity)

        arguments = parameters['arguments']

        if identity in _AWT_INITIALIZERS:
            return self._void()

        if identity == self._REGISTER_NATIVE_LOOPS:
            return self._register_native_loops(parameters['callId'])

        if identity == self._INITIALIZE_RASTER:
            return self._initialize_raster(arguments)

        if identity == self._MASK_BLIT:
            return self._mask_blit(parameters)

        if identity == self._LOAD_PROFILE:
            return self._load_profile(arguments)

        if identity == self._GET_PROFILE_DATA:
            return self._get_profile_data(arguments)

        if identity == self._GET_TAG:
            return self._get_tag(arguments)

        if identity == self._CREATE_TRANSFORM:
            return self._create_transform(arguments)

        if identity == self._COLOR_CONVERT:
            return self._color_convert(arguments)

        raise ValueError(f'unsupported Tika Java native method: {identity}')

    @staticmethod
    def _array(value: dict[str, object], expected_type: str) -> list[int]:
        if value['type'] != expected_type:
            raise ValueError(f'expected {expected_type}, received {value}')

        return value['value']

    @staticmethod
    def _decode_bytes(value: dict[str, object]) -> bytes:
        if value['type'] != 'bytes' or value.get('encoding') != 'base64':
            raise ValueError(f'expected base64 bytes, received {value}')

        return base64.b64decode(value['data'], validate=True)

    @staticmethod
    def _encode_bytes(value: bytes) -> dict[str, str]:
        return {
            'type': 'bytes',
            'encoding': 'base64',
            'data': base64.b64encode(value).decode('ascii'),
        }

    @classmethod
    def _decode_pixel_buffer(
        cls,
        value: dict[str, object],
        buffer_type: int,
        raw_mode: str,
    ) -> bytes:
        if buffer_type == cls._BYTE_BUFFER_TYPE:
            return cls._decode_bytes(value)

        if buffer_type == cls._SHORT_BUFFER_TYPE:
            if value['type'] != 'short[]':
                raise ValueError(f'expected short[], received {value}')

            return b''.join(
                (component & 0xFFFF).to_bytes(2, 'big')
                for component in value['value']
            )

        if buffer_type == cls._INT_BUFFER_TYPE and raw_mode == 'BGRA':
            if value['type'] != 'int[]':
                raise ValueError(f'expected int[], received {value}')

            return b''.join(
                (component & 0xFFFFFFFF).to_bytes(4, 'little')
                for component in value['value']
            )

        raise ValueError(f'unsupported Java2D pixel buffer type: {buffer_type}')

    @classmethod
    def _encode_pixel_buffer(
        cls,
        value: bytes,
        buffer_type: int,
        raw_mode: str,
    ) -> dict[str, object]:
        if buffer_type == cls._BYTE_BUFFER_TYPE:
            return cls._encode_bytes(value)

        if buffer_type == cls._SHORT_BUFFER_TYPE:
            if len(value) % 2:
                raise ValueError('16-bit Java2D pixel data has an odd byte count')

            return {
                'type': 'short[]',
                'value': [
                    int.from_bytes(value[index:index + 2], 'big', signed=True)
                    for index in range(0, len(value), 2)
                ],
            }

        if buffer_type == cls._INT_BUFFER_TYPE and raw_mode == 'BGRA':
            if len(value) % 4:
                raise ValueError('32-bit Java2D pixel data has an odd byte count')

            return {
                'type': 'int[]',
                'value': [
                    int.from_bytes(value[index:index + 4], 'little', signed=True)
                    for index in range(0, len(value), 4)
                ],
            }

        raise ValueError(f'unsupported Java2D pixel buffer type: {buffer_type}')

    @staticmethod
    def _output_pixels(image: Image.Image, layout: _PixelLayout) -> bytes:
        mode, raw_mode, _bytes_per_pixel, buffer_type = layout
        if buffer_type == _TikaHostService._BYTE_BUFFER_TYPE:
            return image.tobytes('raw', raw_mode)

        if raw_mode == 'RGB;16B':
            return b''.join(
                (component * 257).to_bytes(2, 'big')
                for component in image.tobytes('raw', mode)
            )

        raise ValueError(f'unsupported 16-bit Java2D pixel layout: {raw_mode}')

    @classmethod
    def _supports_pixel_buffer_type(
        cls,
        layout: _PixelLayout,
        buffer_type: int,
    ) -> bool:
        _mode, raw_mode, bytes_per_pixel, expected_type = layout
        if buffer_type == expected_type:
            return True

        return (
            buffer_type == cls._INT_BUFFER_TYPE
            and bytes_per_pixel == 4
            and raw_mode == 'BGRA'
        )

    @staticmethod
    def _identity(parameters: dict[str, Any]) -> str:
        return f"{parameters['owner']}.{parameters['name']}{parameters['descriptor']}"

    @staticmethod
    def _integer(value: dict[str, object]) -> int:
        if value['type'] not in ('int', 'long'):
            raise ValueError(f'expected integer, received {value}')

        return value['value']

    @staticmethod
    def _reference(value: dict[str, object]) -> int:
        if value['type'] != 'java-ref':
            raise ValueError(f'expected Java object reference, received {value}')

        return value['id']

    @classmethod
    def _pixel_layout(cls, formatter: int) -> _PixelLayout:
        bytes_per_component = formatter & cls._FORMATTER_BYTES_MASK
        color_channels = (formatter >> cls._FORMATTER_CHANNELS_SHIFT) & 0xf
        extra_channels = (formatter >> cls._FORMATTER_EXTRA_SHIFT) & 0x7
        color_space = (formatter >> cls._FORMATTER_COLOR_SPACE_SHIFT) & 0x1f
        swapped = bool(formatter & cls._FORMATTER_SWAP)
        alpha_first = bool(formatter & cls._FORMATTER_SWAP_FIRST)

        if (
            bytes_per_component == 1
            and color_channels == 1
            and extra_channels == 0
            and color_space in (0, cls._GRAY_COLOR_SPACE)
            and not swapped
            and not alpha_first
        ):
            return 'L', 'L', 1, cls._BYTE_BUFFER_TYPE

        if (
            bytes_per_component == 1
            and color_channels == 3
            and extra_channels == 0
            and color_space in (0, cls._RGB_COLOR_SPACE)
            and not alpha_first
        ):
            return 'RGB', 'BGR' if swapped else 'RGB', 3, cls._BYTE_BUFFER_TYPE

        if (
            bytes_per_component == 1
            and color_channels == 3
            and extra_channels == 1
            and color_space in (0, cls._RGB_COLOR_SPACE)
        ):
            raw_mode = {
                (False, False): 'RGBA',
                (False, True): 'ARGB',
                (True, False): 'ABGR',
                (True, True): 'BGRA',
            }[(swapped, alpha_first)]

            return 'RGBA', raw_mode, 4, cls._BYTE_BUFFER_TYPE

        if formatter == 0x0000001A:
            return 'RGB', 'RGB;16B', 6, cls._SHORT_BUFFER_TYPE

        raise ValueError(f'unsupported LCMS pixel formatter: 0x{formatter:08x}')

    @staticmethod
    def _pixel_region_arguments(
        x: int,
        y: int,
        width: int,
        height: int,
        pixels: list[int] | None = None,
    ) -> list[dict[str, object]]:
        return [
            {'type': 'int', 'value': x},
            {'type': 'int', 'value': y},
            {'type': 'int', 'value': width},
            {'type': 'int', 'value': height},
            {'type': 'null'} if pixels is None else {'type': 'int[]', 'value': pixels},
            {'type': 'int', 'value': 0},
            {'type': 'int', 'value': width},
        ]

    @staticmethod
    def _void() -> dict[str, dict[str, str]]:
        return {'return': {'type': 'void'}}

    def bind_environment(
        self,
        execute: Callable[[int, list[dict[str, object]]], dict[str, object]],
    ) -> None:
        self._execute_environment = execute

    def _allocate_handle(self) -> int:
        handle = self._next_handle
        self._next_handle += 1

        return handle

    def _execute_java_environment(
        self,
        call_id: int,
        operations: list[dict[str, object]],
        operation: str,
    ) -> dict[str, object]:
        if self._execute_environment is None:
            raise RuntimeError(f'Java environment is unavailable for {operation}')

        response = self._execute_environment(call_id, operations)
        if 'javaException' in response:
            raise RuntimeError(f"{operation} failed: {response['javaException']}")

        return response

    def _color_convert(self, arguments: list[dict[str, object]]) -> dict[str, object]:
        handle = self._integer(arguments[0])
        width = self._integer(arguments[1])
        height = self._integer(arguments[2])
        source_offset = self._integer(arguments[3])
        source_stride = self._integer(arguments[4])
        destination_offset = self._integer(arguments[5])
        destination_stride = self._integer(arguments[6])
        source_type = self._integer(arguments[9])
        destination_type = self._integer(arguments[10])

        transform, input_layout, output_layout = self._transform(handle)
        input_mode, input_raw_mode, source_bpp, _input_type = input_layout
        output_mode, output_raw_mode, destination_bpp, _output_type = output_layout
        if not (
            self._supports_pixel_buffer_type(input_layout, source_type)
            and self._supports_pixel_buffer_type(output_layout, destination_type)
        ):
            raise ValueError(
                'Java2D pixel buffer type does not match its LCMS layout: '
                f'{input_raw_mode} uses type {source_type}, '
                f'{output_raw_mode} uses type {destination_type}'
            )

        source = self._decode_pixel_buffer(arguments[7], source_type, input_raw_mode)
        destination = self._decode_pixel_buffer(
            arguments[8],
            destination_type,
            output_raw_mode,
        )

        if source_stride != width * source_bpp or destination_stride != width * destination_bpp:
            raise ValueError('Tika supports only contiguous Java2D pixel rows')

        source_end = source_offset + source_stride * height
        if source_offset < 0 or source_end > len(source):
            raise ValueError('source Java2D pixel buffer is out of bounds')

        image = Image.frombytes(
            input_mode,
            (width, height),
            source[source_offset:source_end],
            'raw',
            input_raw_mode,
        )
        converted = ImageCms.applyTransform(image, transform)
        pixels = self._output_pixels(converted, output_layout)

        destination_end = destination_offset + len(pixels)
        if destination_offset < 0 or destination_end > len(destination):
            raise ValueError('destination Java2D pixel buffer is out of bounds')

        result = bytearray(destination)
        result[destination_offset:destination_end] = pixels

        return {
            'return': {'type': 'void'},
            'mutations': [{
                'argument': 8,
                'value': self._encode_pixel_buffer(
                    result,
                    destination_type,
                    output_raw_mode,
                ),
            }],
        }

    def _create_transform(self, arguments: list[dict[str, object]]) -> dict[str, object]:
        profile_handles = self._array(arguments[0], 'long[]')
        rendering_intent = self._integer(arguments[1])
        input_format = self._integer(arguments[2])
        output_format = self._integer(arguments[3])
        profiles = [self._profile(handle)[1] for handle in profile_handles]
        if len(profiles) != 2:
            raise ValueError('Tika supports one source and one destination ICC profile')

        input_layout = self._pixel_layout(input_format)
        output_layout = self._pixel_layout(output_format)
        input_mode = input_layout[0]
        output_mode = output_layout[0]
        transform = ImageCms.buildTransformFromOpenProfiles(
            profiles[0],
            profiles[1],
            input_mode,
            output_mode,
            renderingIntent=rendering_intent,
        )

        handle = self._allocate_handle()
        self._transforms[handle] = (
            transform,
            input_layout,
            output_layout,
        )
        return {'return': {'type': 'long', 'value': handle}}

    def _get_profile_data(self, arguments: list[dict[str, object]]) -> dict[str, object]:
        profile_data, _profile = self._profile(self._integer(arguments[0]))

        return {'return': self._encode_bytes(profile_data)}

    def _get_tag(self, arguments: list[dict[str, object]]) -> dict[str, object]:
        profile_data, _profile = self._profile(self._integer(arguments[0]))
        signature = self._integer(arguments[1]) & 0xFFFFFFFF
        if signature == self._ICC_HEADER_TAG:
            return {'return': self._encode_bytes(profile_data[:self._ICC_HEADER_SIZE])}

        return {'return': self._encode_bytes(self._profile_tag_data(profile_data, signature))}

    def _initialize_raster(self, arguments: list[dict[str, object]]) -> dict[str, dict[str, str]]:
        if len(arguments) != 8:
            raise ValueError('BufImgSurfaceData.initRaster has the wrong argument count')

        return self._void()

    def _load_profile(self, arguments: list[dict[str, object]]) -> dict[str, object]:
        profile_data = self._decode_bytes(arguments[0])
        if len(profile_data) < 40 or profile_data[36:40] != b'acsp':
            raise ValueError('LCMS received an invalid ICC profile')

        handle = self._allocate_handle()
        self._profiles[handle] = (
            profile_data,
            ImageCms.ImageCmsProfile(BytesIO(profile_data)),
        )
        return {'return': {'type': 'long', 'value': handle}}

    def _mask_blit(self, parameters: dict[str, Any]) -> dict[str, dict[str, str]]:
        arguments = parameters['arguments']
        if len(arguments) != 13:
            raise ValueError('MaskBlit has the wrong argument count')

        if arguments[3]['type'] != 'null':
            raise ValueError('Tika does not yet support clipped MaskBlit operations')

        if arguments[10]['type'] != 'null':
            raise ValueError('Tika does not yet support masked MaskBlit operations')

        source = self._reference(arguments[0])
        destination = self._reference(arguments[1])
        composite = self._reference(arguments[2])
        source_x, source_y, destination_x, destination_y, width, height = (
            self._integer(value) for value in arguments[4:10]
        )

        response = self._execute_java_environment(parameters['callId'], [
            {
                'out': 'surfaceDataClass',
                'op': 'findClass',
                'name': 'sun/awt/image/BufImgSurfaceData',
            },
            {'out': 'bufferedImageClass', 'op': 'findClass', 'name': 'java/awt/image/BufferedImage'},
            {'out': 'alphaCompositeClass', 'op': 'findClass', 'name': 'java/awt/AlphaComposite'},

            {
                'out': 'getDestination',
                'op': 'getMethod',
                'class': {'tmp': 'surfaceDataClass'},
                'name': 'getDestination',
                'descriptor': '()Ljava/lang/Object;',
            },
            {
                'out': 'getRgb',
                'op': 'getMethod',
                'class': {'tmp': 'bufferedImageClass'},
                'name': 'getRGB',
                'descriptor': '(IIII[III)[I',
            },
            {
                'out': 'setRgb',
                'op': 'getMethod',
                'class': {'tmp': 'bufferedImageClass'},
                'name': 'setRGB',
                'descriptor': '(IIII[III)V',
            },
            {
                'out': 'getRule',
                'op': 'getMethod',
                'class': {'tmp': 'alphaCompositeClass'},
                'name': 'getRule',
                'descriptor': '()I',
            },
            {
                'out': 'getAlpha',
                'op': 'getMethod',
                'class': {'tmp': 'alphaCompositeClass'},
                'name': 'getAlpha',
                'descriptor': '()F',
            },

            {
                'out': 'sourceImage',
                'op': 'call',
                'method': {'tmp': 'getDestination'},
                'target': {'ref': source},
            },
            {
                'out': 'destinationImage',
                'op': 'call',
                'method': {'tmp': 'getDestination'},
                'target': {'ref': destination},
            },
            {
                'out': 'rule',
                'op': 'call',
                'method': {'tmp': 'getRule'},
                'target': {'ref': composite},
            },
            {
                'out': 'alpha',
                'op': 'call',
                'method': {'tmp': 'getAlpha'},
                'target': {'ref': composite},
            },
            {
                'out': 'sourcePixels',
                'op': 'call',
                'method': {'tmp': 'getRgb'},
                'target': {'tmp': 'sourceImage'},
                'arguments': self._pixel_region_arguments(
                    source_x,
                    source_y,
                    width,
                    height,
                ),
            },
            {
                'out': 'destinationPixels',
                'op': 'call',
                'method': {'tmp': 'getRgb'},
                'target': {'tmp': 'destinationImage'},
                'arguments': self._pixel_region_arguments(
                    destination_x,
                    destination_y,
                    width,
                    height,
                ),
            },
        ], 'MaskBlit')
        values = response['values']
        pixels = self._composite_pixels(
            self._array(values['sourcePixels'], 'int[]'),
            self._array(values['destinationPixels'], 'int[]'),
            self._integer(values['rule']),
            values['alpha']['value'],
        )
        destination_image = self._reference(values['destinationImage'])

        self._execute_java_environment(parameters['callId'], [
            {'out': 'bufferedImageClass', 'op': 'findClass', 'name': 'java/awt/image/BufferedImage'},
            {
                'out': 'setRgb',
                'op': 'getMethod',
                'class': {'tmp': 'bufferedImageClass'},
                'name': 'setRGB',
                'descriptor': '(IIII[III)V',
            },
            {
                'op': 'call',
                'method': {'tmp': 'setRgb'},
                'target': {'ref': destination_image},
                'arguments': self._pixel_region_arguments(
                    destination_x,
                    destination_y,
                    width,
                    height,
                    pixels,
                ),
            },
        ], 'MaskBlit')

        return self._void()

    def _composite_pixels(
        self,
        source: list[int],
        destination: list[int],
        rule: int,
        alpha: float,
    ) -> list[int]:
        if len(source) != len(destination):
            raise ValueError('MaskBlit source and destination pixel counts differ')

        if rule == self._ALPHA_COMPOSITE_SRC:
            return [self._apply_alpha(pixel, alpha) for pixel in source]

        if rule == self._ALPHA_COMPOSITE_SRC_OVER:
            return [
                self._source_over(source_pixel, destination_pixel, alpha)
                for source_pixel, destination_pixel in zip(source, destination)
            ]

        raise ValueError(f'unsupported AlphaComposite rule: {rule}')

    @staticmethod
    def _apply_alpha(pixel: int, alpha: float) -> int:
        source_alpha = round(((pixel >> 24) & 0xff) * alpha)

        return (source_alpha << 24) | (pixel & 0x00ffffff)

    @staticmethod
    def _source_over(source: int, destination: int, alpha: float) -> int:
        source_alpha = round(((source >> 24) & 0xff) * alpha)
        destination_alpha = (destination >> 24) & 0xff
        inverse_source_alpha = 255 - source_alpha
        output_alpha = source_alpha + (destination_alpha * inverse_source_alpha + 127) // 255
        if output_alpha == 0:
            return 0

        output_channels = []
        for shift in (16, 8, 0):
            source_channel = (source >> shift) & 0xff
            destination_channel = (destination >> shift) & 0xff
            premultiplied = (
                source_channel * source_alpha
                + (destination_channel * destination_alpha * inverse_source_alpha + 127) // 255
            )
            output_channels.append((premultiplied + output_alpha // 2) // output_alpha)

        return (
            (output_alpha << 24)
            | (output_channels[0] << 16)
            | (output_channels[1] << 8)
            | output_channels[2]
        )

    def _register_native_loops(self, call_id: int) -> dict[str, dict[str, str]]:
        operations = [
            {'out': 'maskBlitClass', 'op': 'findClass', 'name': 'sun/java2d/loops/MaskBlit'},
            {'out': 'surfaceTypeClass', 'op': 'findClass', 'name': 'sun/java2d/loops/SurfaceType'},
            {'out': 'compositeTypeClass', 'op': 'findClass', 'name': 'sun/java2d/loops/CompositeType'},
            {
                'out': 'graphicsPrimitiveClass',
                'op': 'findClass',
                'name': 'sun/java2d/loops/GraphicsPrimitive',
            },
            {
                'out': 'graphicsPrimitiveManagerClass',
                'op': 'findClass',
                'name': 'sun/java2d/loops/GraphicsPrimitiveMgr',
            },

            {
                'out': 'intArgbField',
                'op': 'getField',
                'class': {'tmp': 'surfaceTypeClass'},
                'name': 'IntArgb',
            },
            {
                'out': 'intArgb',
                'op': 'readStaticField',
                'field': {'tmp': 'intArgbField'},
            },
            {
                'out': 'anyAlphaField',
                'op': 'getField',
                'class': {'tmp': 'compositeTypeClass'},
                'name': 'AnyAlpha',
            },
            {
                'out': 'anyAlpha',
                'op': 'readStaticField',
                'field': {'tmp': 'anyAlphaField'},
            },

            {
                'out': 'maskBlitConstructor',
                'op': 'getMethod',
                'class': {'tmp': 'maskBlitClass'},
                'name': '<init>',
                'descriptor': (
                    '(JLsun/java2d/loops/SurfaceType;'
                    'Lsun/java2d/loops/CompositeType;'
                    'Lsun/java2d/loops/SurfaceType;)V'
                ),
            },
            {
                'out': 'maskBlit',
                'op': 'newObject',
                'method': {'tmp': 'maskBlitConstructor'},
                'arguments': [
                    {'type': 'long', 'value': 0},
                    {'tmp': 'intArgb'},
                    {'tmp': 'anyAlpha'},
                    {'tmp': 'intArgb'},
                ],
            },

            {
                'out': 'primitives',
                'op': 'newObjectArray',
                'component': {'tmp': 'graphicsPrimitiveClass'},
                'length': 1,
            },
            {
                'op': 'setObjectArrayElement',
                'array': {'tmp': 'primitives'},
                'index': 0,
                'value': {'tmp': 'maskBlit'},
            },
            {
                'out': 'register',
                'op': 'getMethod',
                'class': {'tmp': 'graphicsPrimitiveManagerClass'},
                'name': 'register',
                'descriptor': '([Lsun/java2d/loops/GraphicsPrimitive;)V',
            },
            {
                'op': 'callStatic',
                'method': {'tmp': 'register'},
                'arguments': [{'tmp': 'primitives'}],
            },
        ]
        self._execute_java_environment(call_id, operations, 'native loop registration')

        return self._void()

    def _profile(self, handle: int) -> tuple[bytes, ImageCms.ImageCmsProfile]:
        profile = self._profiles.get(handle)
        if profile is None:
            raise ValueError(f'unknown ICC profile handle: {handle}')

        return profile

    def _profile_tag_data(self, profile_data: bytes, signature: int) -> bytes:
        tag_count = int.from_bytes(
            profile_data[self._ICC_TAG_TABLE_OFFSET:self._ICC_TAG_TABLE_OFFSET + 4],
            'big',
        )
        for index in range(tag_count):
            entry_offset = self._ICC_TAG_TABLE_OFFSET + 4 + index * self._ICC_TAG_ENTRY_SIZE
            entry_end = entry_offset + self._ICC_TAG_ENTRY_SIZE
            if entry_end > len(profile_data):
                break

            tag = int.from_bytes(profile_data[entry_offset:entry_offset + 4], 'big')
            data_offset = int.from_bytes(profile_data[entry_offset + 4:entry_offset + 8], 'big')
            data_length = int.from_bytes(profile_data[entry_offset + 8:entry_end], 'big')
            data_end = data_offset + data_length
            if tag == signature and data_end <= len(profile_data):
                return profile_data[data_offset:data_end]

        raise ValueError(f'ICC profile does not contain tag: 0x{signature:08x}')

    def _transform(self, handle: int) -> tuple[Any, _PixelLayout, _PixelLayout]:
        transform = self._transforms.get(handle)
        if transform is None:
            raise ValueError(f'unknown ICC transform handle: {handle}')

        return transform


class _HostServer:
    """Own the Java APE JSON-RPC Host Services connection."""

    def __init__(self, token: str) -> None:
        self._token = token
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(('127.0.0.1', 0))
        self._listener.listen(1)
        self._listener.settimeout(0.25)
        self._closed = threading.Event()
        self._endpoint: Endpoint | None = None
        self._thread: threading.Thread | None = None
        self.service = _TikaHostService()

    @property
    def address(self) -> str:
        return f'127.0.0.1:{self._listener.getsockname()[1]}'

    def start(self) -> None:
        if self._thread is not None:
            return

        self._thread = threading.Thread(
            target=self._serve,
            name='tika-ape-host-services',
            daemon=True,
        )
        self._thread.start()

    def close(self) -> None:
        self._closed.set()
        self._listener.close()

        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def _initialize(self, parameters: dict[str, Any]) -> dict[str, object]:
        if parameters['protocolVersions'] != ['1.0']:
            raise ValueError('unexpected host protocol versions')

        if parameters['runtime']['name'] != 'java-ape':
            raise ValueError('unexpected host runtime')

        if parameters['token'] != self._token:
            raise ValueError('unexpected host token')

        return {'protocolVersion': '1.0', 'capabilities': ['java.native', 'java.env']}

    def _execute_environment(
        self,
        call_id: int,
        operations: list[dict[str, object]],
    ) -> dict[str, object]:
        if self._endpoint is None:
            raise RuntimeError('Java environment is unavailable before Host Services initialization')

        return self._endpoint.request(
            'java.env.execute',
            {'callId': call_id, 'ops': operations},
        ).result(timeout=10)

    def _native_invoke(self, parameters: dict[str, Any]) -> Any:
        return lambda: self.service.replace_native_method(parameters)

    def _serve(self) -> None:
        while not self._closed.is_set():
            try:
                connection, _peer_address = self._listener.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                if self._closed.is_set():
                    return

                raise

            self._serve_connection(connection)

    def _serve_connection(self, connection: socket.socket) -> None:
        with connection:
            with connection.makefile('rb') as input_stream:
                with connection.makefile('wb') as output_stream:
                    reader = JsonRpcStreamReader(input_stream)
                    writer = JsonRpcStreamWriter(output_stream)
                    self._endpoint = Endpoint(
                        {
                            'host.initialize': self._initialize,
                            'java.native.invoke': self._native_invoke,
                        },
                        writer.write,
                    )
                    self.service.bind_environment(self._execute_environment)
                    listener_thread = threading.Thread(
                        target=self._listen,
                        args=(reader,),
                    )
                    listener_thread.start()
                    listener_thread.join()
                    self._endpoint.shutdown()

    def _listen(self, reader: JsonRpcStreamReader) -> None:
        try:
            reader.listen(self._endpoint.consume)
        except ConnectionResetError:
            return


class _TikaHostServices:
    """Own the localhost provider used by the Python-native API."""

    def __init__(self) -> None:
        self._token = base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')
        self._server = _HostServer(self._token)
        self._client = _HostEnabledAPEClient({
            'APE_HOST': self._server.address,
            'APE_HOST_TOKEN': self._token,
            'APE_VIRTUAL_LIBRARIES': 'awt,lcms,fontmanager',
            'JDK_JAVA_OPTIONS': (
                '--add-exports=java.desktop/sun.java2d.loops=ALL-UNNAMED '
                '--add-opens=java.desktop/sun.java2d.loops=ALL-UNNAMED '
                '--add-opens=java.desktop/sun.awt.image=ALL-UNNAMED'
            ),
        })

    def start(self) -> None:
        self._server.start()

    def close(self) -> None:
        self._server.close()

    def invoke(self, operation: str, options: dict[str, Any]) -> Any:
        return self._client.invoke(operation, options)

    def raw(self, arguments: list[str]) -> Any:
        return self._client.raw(arguments)
