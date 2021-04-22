# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import math
from contextlib import ExitStack
from itertools import count
from subprocess import PIPE

import numpy

import marv_api as marv
from marv_api.types import File
from marv_api.utils import popen
from marv_ros.img_tools import (ImageConversionError, ImageFormatError, compressed_imgmsg_to_cv2,
                                imgmsg_to_cv2)

from .bag import make_deserialize, messages

try:
    import cv2
except ImportError:
    cv2 = None


IMAGE_MSG_TYPES = ','.join([
    '*:sensor_msgs/Image',
    '*:sensor_msgs/CompressedImage',
    '*:sensor_msgs/msg/Image',
    '*:sensor_msgs/msg/CompressedImage',
])


def ros2cv(msg, scale=1, offset=0):
    if hasattr(msg, 'format'):
        return compressed_imgmsg_to_cv2(msg)

    if 'FC' in msg.encoding:
        passimg = numpy.nan_to_num(imgmsg_to_cv2(msg))
        valscaled = cv2.convertScaleAbs(passimg, None, scale, offset)
        return valscaled

    mono = msg.encoding.startswith('mono') or msg.encoding[-1] in ['1', 'U', 'S', 'F']
    return imgmsg_to_cv2(msg, 'mono8' if mono else 'bgr8')


@marv.node(File, version=1)
@marv.input('stream', foreach=marv.select(messages, IMAGE_MSG_TYPES))
@marv.input('speed', default=4)
@marv.input('convert_32FC1_scale', default=1)
@marv.input('convert_32FC1_offset', default=0)
def ffmpeg(stream, speed, convert_32FC1_scale, convert_32FC1_offset):  # pylint: disable=invalid-name
    """Create video for each sensor_msgs/Image topic with ffmpeg."""
    # pylint: disable=too-many-locals

    yield marv.set_header(title=stream.topic)
    name = f"{stream.topic.replace('/', '_')[1:]}.webm"
    video = yield marv.make_file(name)
    duration = (stream.end_time - stream.start_time) * 1e-9
    framerate = (stream.msg_count / duration) if duration else 1

    deserialize = make_deserialize(stream)
    with ExitStack() as stack:
        encoder = None
        dims = None
        while True:
            msg = yield marv.pull(stream)
            if msg is None:
                break

            rosmsg = deserialize(msg.data)
            try:
                img = ros2cv(rosmsg, convert_32FC1_scale, convert_32FC1_offset)
            except (ImageFormatError, ImageConversionError) as err:
                log = yield marv.get_logger()
                log.error('could not convert image from topic %s: %s ', stream.topic, err)
                return

            if not encoder:
                dims = img.shape[:2]
                ffargs = [
                    'ffmpeg',
                    '-f', 'rawvideo',
                    '-pixel_format', 'gray' if len(img.shape) == 2 else 'bgr24',
                    '-video_size', f'{img.shape[1]}x{img.shape[0]}',
                    '-framerate', str(framerate),
                    '-i', '-',
                    '-c:v', 'libvpx-vp9',
                    '-keyint_min', '25', '-g', '25',
                    '-tile-columns', '4', '-frame-parallel', '1',
                    '-an', '-f', 'webm', '-dash', '1',
                    '-pix_fmt', 'yuv420p',
                    '-loglevel', 'error',
                    '-threads', '8',
                    '-speed', str(speed),
                    '-y',
                    video.path,
                ]
                encoder = stack.enter_context(popen(ffargs, stdin=PIPE))
            if dims != img.shape[:2]:
                log = yield marv.get_logger()
                log.warning(f'could not encode, image size changed {dims} != {img.shape[:2]}')
                return

            encoder.stdin.write(img)

    yield video


@marv.node(File, version=1)
@marv.input('stream', foreach=marv.select(messages, IMAGE_MSG_TYPES))
@marv.input('image_width', default=320)
@marv.input('max_frames', default=50)
@marv.input('convert_32FC1_scale', default=1)
@marv.input('convert_32FC1_offset', default=0)
def images(stream, image_width, max_frames, convert_32FC1_scale, convert_32FC1_offset):
    """Extract max_frames equidistantly spread images from each sensor_msgs/Image stream.

    Args:
        stream: sensor_msgs/Image stream
        image_width (int): Scale to image_width, keeping aspect ratio.
        max_frames (int): Maximum number of frames to extract.
        convert_32FC1_scale (float): Scale factor for FC image values.
        convert_32FC1_offset (float): Offset for FC image values.

    """
    # pylint: disable=invalid-name,too-many-locals

    yield marv.set_header(title=stream.topic)
    deserialize = make_deserialize(stream)
    interval = int(math.ceil(stream.msg_count / max_frames))
    digits = int(math.ceil(math.log(stream.msg_count) / math.log(10)))
    name_template = '%s-{:0%sd}.jpg' % (stream.topic.replace('/', ':')[1:], digits)
    counter = count()
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        idx = next(counter)
        if idx % interval:
            continue

        rosmsg = deserialize(msg.data)
        try:
            img = ros2cv(rosmsg, convert_32FC1_scale, convert_32FC1_offset)
        except (ImageFormatError, ImageConversionError) as err:
            log = yield marv.get_logger()
            log.error('could not convert image from topic %s: %s ', stream.topic, err)
            return

        height = int(round(image_width * img.shape[0] / img.shape[1]))
        scaled_img = cv2.resize(img, (image_width, height),
                                interpolation=cv2.INTER_AREA)
        name = name_template.format(idx)
        imgfile = yield marv.make_file(name)
        cv2.imwrite(imgfile.path, scaled_img, (cv2.IMWRITE_JPEG_QUALITY, 60))
        yield imgfile
