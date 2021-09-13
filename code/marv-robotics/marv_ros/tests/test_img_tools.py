# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import struct
from base64 import b64decode

import numpy
import pytest
from rosbags.typesys.types import sensor_msgs__msg__CompressedImage as CompressedImage
from rosbags.typesys.types import sensor_msgs__msg__Image as Image

from marv_ros.img_tools import ImageConversionError, compressed_imgmsg_to_cv2, imgmsg_to_cv2

FORMATS = [
    'rgb8',
    'rgba8',
    'rgb16',
    'rgba16',
    'bgr8',
    'bgra8',
    'bgr16',
    'bgra16',
    'mono8',
    'mono16',
    '8UC1',
    '8UC2',
    '8UC3',
    '8UC4',
    '8SC1',
    '8SC2',
    '8SC3',
    '8SC4',
    '16UC1',
    '16UC2',
    '16UC3',
    '16UC4',
    '16SC1',
    '16SC2',
    '16SC3',
    '16SC4',
    '32SC1',
    '32SC2',
    '32SC3',
    '32SC4',
    '32FC1',
    '32FC2',
    '32FC3',
    '32FC4',
    '64FC1',
    '64FC2',
    '64FC3',
    '64FC4',
    'bayer_rggb8',
    'bayer_bggr8',
    'bayer_gbrg8',
    'bayer_grbg8',
    'bayer_rggb16',
    'bayer_bggr16',
    'bayer_gbrg16',
    'bayer_grbg16',
    'yuv422',
]


def get_desc(name):
    if name[0:4] in ('rgba', 'bgra') or name.endswith('C4'):
        channels = 4
    elif name[0:3] in ('rgb', 'bgr') or name.endswith('C3'):
        channels = 3
    elif name.endswith('C2') or name == 'yuv422':
        channels = 2
    elif name.startswith('mono') or name.startswith('bayer_') or name.endswith('C1'):
        channels = 1
    else:
        raise ValueError(f'Unexpected encoding {name}')

    if name.startswith('8') or name.endswith('8') or name == 'yuv422':
        bits = 8
    elif name.startswith('16') or name.endswith('16'):
        bits = 16
    elif name.startswith('32'):
        bits = 32
    elif name.startswith('64'):
        bits = 64
    else:
        raise ValueError(f'Unexpected encoding {name}')

    return (channels, bits, 'FC' in name)


def generate_image(format):
    channels, bits, is_float = get_desc(format)
    width, height = 32, 24

    pxsize = channels * bits >> 3
    step = width * pxsize

    # create empty image and set the first channel of one singular pixel to 0.25 of max value
    data = bytearray(height * step)
    pxpos = step * int(height / 2 - 1) + pxsize * int(width / 2 - 1)
    ftype = {True: {32: 'f', 64: 'd'}, False: {8: 'B', 16: 'H', 32: 'I', 64: 'Q'}}[is_float][bits]
    val = (1 << bits - 2)
    data[pxpos:pxpos+bits >> 8] = struct.pack(f'<{ftype}', val)

    # set remaining channels to 0, tests use this source value to check encoding conversions
    val = val if channels == 1 else numpy.array([val] + [0] * (channels - 1))

    return Image(header=None, height=height, width=width, encoding=format, is_bigendian=False,
                 step=step, data=data), bits, val


@pytest.mark.parametrize('format', FORMATS)
def test_noconvert(format):
    image, _, val = generate_image(format)
    img = imgmsg_to_cv2(image, dst_encoding=None)
    assert img.shape[0:2] == (image.height, image.width)
    numpy.testing.assert_array_equal(img[11:13, 15:17], [[val, val*0], [val*0, val*0]])


@pytest.mark.parametrize('format', FORMATS)
def test_convert_mono(format):
    image, bits, val = generate_image(format)

    # unsupported auto conversions
    if format[-2:] in ('C2', 'C3', 'C4', '22'):
        with pytest.raises(ImageConversionError):
            imgmsg_to_cv2(image, 'mono8')
        return

    img = imgmsg_to_cv2(image, 'mono8')
    assert img.shape == (image.height, image.width)

    # apply CCIR 601
    if format.startswith('rgb'):
        val = int(val[0] * 0.2989)
    elif format.startswith('bgr'):
        val = int(val[0] * 0.1140)

    # 16 bits are autoscaled down, higher bits do not fit into uint8
    if bits == 16:
        val = int(val / 257)
    elif bits > 16:
        val = 0

    if format.startswith('bayer_rggb'):
        expect = [[7, 4 - (bits == 16)], [3, 2 - (bits == 16)]]
    elif format.startswith('bayer_bggr'):
        expect = [[19, 10 - (bits == 16)], [9, 5 - (bits == 16)]]
    elif format.startswith('bayer_g'):
        expect = [[37, 9], [9, 0]]
    else:
        expect = [[val, val*0], [val*0, val*0]]

    numpy.testing.assert_array_equal(img[11:13, 15:17], expect)


@pytest.mark.parametrize('format', FORMATS)
def test_convert_bgr8(format):  # noqa: C901
    image, bits, val = generate_image(format)

    # unsupported auto conversions
    if format[-2:] in ('C1', 'C2', 'C4'):
        with pytest.raises(ImageConversionError):
            imgmsg_to_cv2(image, 'bgr8')
        return

    img = imgmsg_to_cv2(image, 'bgr8')
    assert img.shape == (image.height, image.width, 3)

    # flip rgb, remove alpha, expand mono
    if format.startswith('rgb'):
        val = numpy.flip(val[:3])
    elif format.startswith('bgr'):
        val = val[:3]
    elif format.startswith('mono'):
        val = numpy.array([val, val, val])

    if bits == 16 and not isinstance(val, int):
        val = (val / 257).astype(int)
    elif bits > 16:
        val = val * 0
    if format.startswith('bayer_rggb'):
        expect = [
            [[64 - (bits == 16), 0, 0], [32 - (bits == 16), 0, 0]],
            [[32 - (bits == 16), 0, 0], [16 - (bits == 16), 0, 0]],
        ]
    elif format.startswith('bayer_bggr'):
        expect = [
            [[0, 0, 64 - (bits == 16)], [0, 0, 32 - (bits == 16)]],
            [[0, 0, 32 - (bits == 16)], [0, 0, 16 - (bits == 16)]],
        ]
    elif format.startswith('bayer_g'):
        expect = [
            [[0, 64 - (bits == 16), 0], [0, 16 - (bits == 16), 0]],
            [[0, 16 - (bits == 16), 0], [0, 0, 0]],
        ]
    elif format == 'yuv422':
        expect = [[[0, 102, 0], [0, 154, 0]], [[0, 154, 0], [0, 154, 0]]]
    else:
        expect = [[val, val*0], [val*0, val*0]]

    numpy.testing.assert_array_equal(img[11:13, 15:17], expect)


def test_compressed_png():
    image = CompressedImage(None, 'png', b64decode("""
        iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9
        awAAAABJRU5ErkJggg==
    """))
    img = compressed_imgmsg_to_cv2(image, 'bgr8')
    numpy.testing.assert_array_equal(img, [[[0, 255, 0]]])


def test_compressed_jpg():
    image = CompressedImage(None, 'jpeg', b64decode("""
        /9j/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8Q
        EBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2gAIAQEAAD8A0s8g/9k=
    """))
    img = compressed_imgmsg_to_cv2(image, 'bgr8')
    numpy.testing.assert_array_equal(img, [[190]])
