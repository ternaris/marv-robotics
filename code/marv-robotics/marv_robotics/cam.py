# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import math
import subprocess
from itertools import count

import cv_bridge
import cv2
import marv
import numpy

from marv.types import File
from .bag import get_message_type, messages

imgmsg_to_cv2 = cv_bridge.CvBridge().imgmsg_to_cv2


@marv.node(File)
@marv.input('stream', foreach=marv.select(messages, '*:sensor_msgs/Image'))
@marv.input('speed', default=4)
@marv.input('convert_32FC1_scale', default=1)
@marv.input('convert_32FC1_offset', default=0)
def ffmpeg(stream, speed, convert_32FC1_scale, convert_32FC1_offset):
    """Create video for each sensor_msgs/Image topic with ffmpeg"""
    yield marv.set_header(title=stream.topic)
    name = '{}.webm'.format(stream.topic.replace('/', '_')[1:])
    video = yield marv.make_file(name)
    duration = (stream.end_time - stream.start_time) * 1e-9
    framerate = stream.msg_count / duration

    pytype = get_message_type(stream)
    rosmsg = pytype()

    encoder = None
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        rosmsg.deserialize(msg.data)
        if not encoder:
            ffargs = [
                'ffmpeg',
                '-f', 'rawvideo',
                '-pixel_format', '%s' % {'mono8': 'gray',
                                         '32FC1': 'gray',
                                         '8UC1': 'gray'}.get(rosmsg.encoding, 'rgb24'),
                '-video_size', '%dx%d' % (rosmsg.width, rosmsg.height),
                '-framerate', '%s' % framerate,
                '-i', '-',
                '-c:v', 'libvpx-vp9',
                '-pix_fmt', 'yuv420p',
                '-loglevel', 'error',
                '-threads', '8',
                '-speed', str(speed),
                '-y',
                video.path,
            ]
            encoder = subprocess.Popen(ffargs, stdin=subprocess.PIPE)

        if rosmsg.encoding == 'mono8':
            data = rosmsg.data
        elif rosmsg.encoding == '32FC1':
            data = cv2.convertScaleAbs(numpy.nan_to_num(imgmsg_to_cv2(rosmsg, 'passthrough')),
                                       None, convert_32FC1_scale, convert_32FC1_offset)
        elif rosmsg.encoding == '8UC1':
            data = imgmsg_to_cv2(rosmsg).tobytes()
        else:
            data = imgmsg_to_cv2(rosmsg, 'rgb8').tobytes()
        encoder.stdin.write(data)

    encoder.stdin.close()
    encoder.wait()
    yield video


@marv.node(File)
@marv.input('stream', foreach=marv.select(messages, '*:sensor_msgs/Image'))
@marv.input('image_width', default=320)
@marv.input('max_frames', default=50)
@marv.input('convert_32FC1_scale', default=1)
@marv.input('convert_32FC1_offset', default=0)
def images(stream, image_width, max_frames, convert_32FC1_scale, convert_32FC1_offset):
    """
    Extract max_frames equidistantly spread images from each sensor_msgs/Image stream.

    Args:
        stream: sensor_msgs/Image stream
        image_width (int): Scale to image_width, keeping aspect ratio.
        max_frames (int): Maximum number of frames to extract.
    """
    yield marv.set_header(title=stream.topic)
    pytype = get_message_type(stream)
    rosmsg = pytype()
    interval = int(math.ceil(stream.msg_count / max_frames))
    digits = int(math.ceil(math.log(stream.msg_count) / math.log(10)))
    name_template = '%s-{:0%sd}.jpg' % (stream.topic.replace('/', ':')[1:], digits)
    counter = count()
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        idx = counter.next()
        if idx % interval:
            continue

        rosmsg.deserialize(msg.data)
        if rosmsg.encoding == '32FC1':
            img = cv2.convertScaleAbs(numpy.nan_to_num(imgmsg_to_cv2(rosmsg, 'passthrough')),
                                      None, convert_32FC1_scale, convert_32FC1_offset)
        elif rosmsg.encoding == '8UC1':
            img = imgmsg_to_cv2(rosmsg)
        else:
            img = imgmsg_to_cv2(rosmsg, "bgr8")
        height = int(round(image_width * img.shape[0] / img.shape[1]))
        scaled_img = cv2.resize(img, (image_width, height),
                                interpolation=cv2.INTER_AREA)
        name = name_template.format(idx)
        imgfile = yield marv.make_file(name)
        cv2.imwrite(imgfile.path, scaled_img, (cv2.IMWRITE_JPEG_QUALITY, 60))
        yield imgfile
