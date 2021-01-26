# Copyright 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import enum
import itertools
import re
import sys

import cv2
import numpy as np


class ImageFormatError(TypeError):
    """Unsupported Image Format."""


class ImageConversionError(TypeError):
    """Unsupported Image Conversion."""


class Format(enum.IntEnum):
    """Supported Image Formats."""

    GENERIC = -1
    GRAY = 0
    RGB = 1
    BGR = 2
    RGBA = 3
    BGRA = 4
    YUV = 5
    BAYER_RG = 6
    BAYER_BG = 7
    BAYER_GB = 8
    BAYER_GR = 9


CONVERSIONS = {
    key: getattr(cv2, f'COLOR_{n1}2{n2}{({"YUV": "_Y422"}).get(n1, "")}', None)
    for key in itertools.product(*(2 * (list(Format)[1:], )))
    if (n1 := key[0].name) == (n2 := key[1].name) or hasattr(cv2, f'COLOR_{n1}2{n2}')
}

DEPTHMAP = {'8U': 'uint8', '8S': 'int8', '16U': 'uint16', '16S': 'int16',
            '32S': 'int32', '32F': 'float32', '64F': 'float64'}

ENCODINGMAP = {
    'mono8': (8, Format.GRAY, 'uint8', 1),
    'bayer_rggb8': (8, Format.BAYER_BG, 'uint8', 1),
    'bayer_bggr8': (8, Format.BAYER_RG, 'uint8', 1),
    'bayer_gbrg8': (8, Format.BAYER_GR, 'uint8', 1),
    'bayer_grbg8': (8, Format.BAYER_GB, 'uint8', 1),
    'yuv422': (8, Format.YUV, 'uint8', 2),
    'bgr8': (8, Format.BGR, 'uint8', 3),
    'rgb8': (8, Format.RGB, 'uint8', 3),
    'bgra8': (8, Format.BGRA, 'uint8', 4),
    'rgba8': (8, Format.RGBA, 'uint8', 4),
    'mono16': (16, Format.GRAY, 'uint16', 1),
    'bayer_rggb16': (16, Format.BAYER_BG, 'uint16', 1),
    'bayer_bggr16': (16, Format.BAYER_RG, 'uint16', 1),
    'bayer_gbrg16': (16, Format.BAYER_GR, 'uint16', 1),
    'bayer_grbg16': (16, Format.BAYER_GB, 'uint16', 1),
    'bgr16': (16, Format.BGR, 'uint16', 3),
    'rgb16': (16, Format.RGB, 'uint16', 3),
    'bgra16': (16, Format.BGRA, 'uint16', 4),
    'rgba16': (16, Format.RGBA, 'uint16', 4),
}


def to_cvtype(encoding):
    """Get typeinfo for encoding."""
    try:
        return ENCODINGMAP[encoding]
    except KeyError:
        pass

    mat = re.fullmatch('(8U|8S|16U|16S|32S|32F|64F)C([0-9]+)', encoding)
    if mat:
        depth, nchan = mat.groups()
        return (int(re.search(r'^\d+', depth).group()), Format.GENERIC, DEPTHMAP[depth], int(nchan))

    mat = re.fullmatch('(8U|8S|16U|16S|32S|32F|64F)', encoding)
    if mat:
        return (int(re.search(r'^\d+', depth).group()), Format.GENERIC, DEPTHMAP[depth], 1)

    raise ImageFormatError(f'Format {encoding} is not supported')


def convert_color(src, src_encoding, dst_encoding):
    """Convert image format."""
    if src_encoding == dst_encoding:
        return src

    src_depth, src_fmt, src_typestr, src_nchan = to_cvtype(src_encoding)
    dst_depth, dst_fmt, dst_typestr, dst_nchan = to_cvtype(dst_encoding)

    try:
        conversion = CONVERSIONS[(src_fmt, dst_fmt)]
    except KeyError:
        if (src_fmt == Format.GENERIC or dst_fmt == Format.GENERIC) and src_nchan == dst_nchan:
            conversion = None
        else:
            raise ImageConversionError(f'Conversion {src_encoding} -> {dst_encoding} not supported')

    if conversion is not None:
        src = cv2.cvtColor(src, conversion)

    if src_typestr != dst_typestr:
        if src_depth == 8 and dst_depth == 16:
            src = src.astype(dst_typestr, copy=False) * 65535. / 255.
        elif src_depth == 16 and dst_depth == 8:
            src = (src * 255. / 65535.).astype(dst_typestr, copy=False)
        else:
            src = src.astype(dst_typestr, copy=False)
    return src


def imgmsg_to_cv2(msg, dst_encoding=None):
    """Convert sensor_msg/Image to cv2."""
    _, _, typestr, nchan = to_cvtype(msg.encoding)
    shape = (msg.height, msg.width) if nchan == 1 else (msg.height, msg.width, nchan)
    dtype = np.dtype(typestr).newbyteorder('>' if msg.is_bigendian else '<')
    img = np.ndarray(shape=shape, dtype=dtype, buffer=msg.data)

    if msg.is_bigendian == (sys.byteorder == 'little'):
        img.byteswap(inplace=True)

    if dst_encoding:
        return convert_color(img, msg.encoding, dst_encoding)
    return img


def compressed_imgmsg_to_cv2(msg, dst_encoding=None):
    """Convert sensor_msg/CompressedImage to cv2."""
    img = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_ANYCOLOR)
    if dst_encoding:
        return convert_color(img, 'bgr8', dst_encoding)
    return img
