# -*- coding: utf-8 -*-
#
# This file is part of MARV Robotics
#
# Copyright 2016 Ternaris
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

import math
from collections import defaultdict

import cv_bridge
import cv2
import marv


imgmsg_to_cv2 = cv_bridge.CvBridge().imgmsg_to_cv2


@marv.node()
@marv.input('bagmeta')
@marv.input('messages', filter=['*:sensor_msgs/Image'])
@marv.param('image_width', help="Scale to image_width, keeping aspect ratio")
@marv.param('max_frames', help="Maximum number of frames to extract")
def camera_frames(bagmeta, messages, image_width=320, max_frames=50):
    """Extract camera frames from sensors_msgs/Image streams

    Images are scaled to image_width while keeping the aspect ratio
    and a maximum of max_frames equidistantly spread frames is
    extracted from each stream.
    """
    # Message counts and desired intervals for all topics. All topics,
    # as we cannot know which topics a user configured.
    message_counts = {k: v['message_count'] for k, v in bagmeta.topics.items()}
    intervals = {topic: int(math.ceil(message_count / max_frames))
                 for topic, message_count in message_counts.items()}

    # Keep track of per-topic message indices and images generated
    msg_indices = defaultdict(int)
    images = defaultdict(list)
    for topic, msg, _ in messages:

        # Only use messages in desired per-topic intervals
        idx = msg_indices[topic]
        msg_indices[topic] = idx + 1
        if idx % intervals[topic]:
            continue

        try:
            img = imgmsg_to_cv2(msg, "rgb8")
        except:
            import traceback
            marv.log_error('On topic %r: %s', topic, traceback.format_exc())
            continue

        # Instruct marv to create a file for the current image:
        # image_path is for us to work with the file, image_id we
        # return so marv knows what we are talking about.  The
        # location we are writing to is not the same as the one the
        # image will be served from later on.
        image_name = '{name}_{idx:03d}.jpg'.format(name=topic.replace('/', '_')[1:],
                                                   idx=idx // intervals[topic])
        image_path, image_id = marv.make_file(image_name)

        # We return a mapping of topics to image lists for
        # e.g. per-topic galleries to be rendered
        images[topic].append(image_id)

        # scale image and write to disk
        height = int(round(image_width * img.shape[0] / img.shape[1]))
        scaled_img = cv2.resize(img, (image_width, height),
                                interpolation=cv2.INTER_AREA)
        cv2.imwrite(image_path, scaled_img, (cv2.IMWRITE_JPEG_QUALITY, 60))

    # return mapping of topics to image lists
    return images
