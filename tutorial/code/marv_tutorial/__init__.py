# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: CC0-1.0

import json
import os

import cv2
import cv_bridge
import matplotlib.pyplot as plt
import mpld3
imgmsg_to_cv2 = cv_bridge.CvBridge().imgmsg_to_cv2

import marv
from marv_detail.types_capnp import Section, Widget  # pylint: disable=no-name-in-module
from marv_nodes.types_capnp import File  # pylint: disable=no-name-in-module
from marv_robotics.bag import get_message_type, raw_messages

TOPIC = '/wide_stereo/left/image_rect_throttle'

# pylint: disable=redefined-outer-name


@marv.node(File)
@marv.input('cam', marv.select(raw_messages, TOPIC))
def image(cam):
    """Extract first image of input stream to jpg file.

    Args:
        cam: Input stream of raw rosbag messages.

    Returns:
        File instance for first image of input stream.
    """
    # Set output stream title and pull first message
    yield marv.set_header(title=cam.topic)
    msg = yield marv.pull(cam)
    if msg is None:
        return

    # Deserialize raw ros message
    pytype = get_message_type(cam)
    rosmsg = pytype()
    rosmsg.deserialize(msg.data)

    # Write image to jpeg and push it to output stream
    name = f"{cam.topic.replace('/', ':')[1:]}.jpg"
    imgfile = yield marv.make_file(name)
    img = imgmsg_to_cv2(rosmsg, "rgb8")
    cv2.imwrite(imgfile.path, img, (cv2.IMWRITE_JPEG_QUALITY, 60))
    yield marv.push(imgfile)


@marv.node(Section)
@marv.input('title', default='Image')
@marv.input('image', default=image)
def image_section(image, title):
    """Create detail section with one image.

    Args:
        title (str): Title to be displayed for detail section.
        image: marv image file.

    Returns
        One detail section.
    """
    # pull first image
    img = yield marv.pull(image)
    if img is None:
        return

    # create image widget and section containing it
    widget = {'title': image.title, 'image': {'src': img.relpath}}
    section = {'title': title, 'widgets': [widget]}
    yield marv.push(section)


@marv.node(File)
@marv.input('cam', marv.select(raw_messages, TOPIC))
def images(cam):
    """Extract images from input stream to jpg files.

    Args:
        cam: Input stream of raw rosbag messages.

    Returns:
        File instances for images of input stream.
    """
    # Set output stream title and pull first message
    yield marv.set_header(title=cam.topic)

    # Fetch and process first 20 image messages
    name_template = '%s-{}.jpg' % cam.topic.replace('/', ':')[1:]
    while True:
        idx, msg = yield marv.pull(cam, enumerate=True)
        if msg is None or idx >= 20:
            break

        # Deserialize raw ros message
        pytype = get_message_type(cam)
        rosmsg = pytype()
        rosmsg.deserialize(msg.data)

        # Write image to jpeg and push it to output stream
        img = imgmsg_to_cv2(rosmsg, "rgb8")
        name = name_template.format(idx)
        imgfile = yield marv.make_file(name)
        cv2.imwrite(imgfile.path, img)
        yield marv.push(imgfile)


@marv.node(Section)
@marv.input('title', default='Gallery')
@marv.input('images', default=images)
def gallery_section(images, title):
    """Create detail section with gallery.

    Args:
        title (str): Title to be displayed for detail section.
        images: stream of marv image files

    Returns
        One detail section.
    """
    # pull all images
    imgs = []
    while True:
        img = yield marv.pull(images)
        if img is None:
            break
        imgs.append({'src': img.relpath})
    if not imgs:
        return

    # create gallery widget and section containing it
    widget = {'title': images.title, 'gallery': {'images': imgs}}
    section = {'title': title, 'widgets': [widget]}
    yield marv.push(section)


@marv.node()
@marv.input('images', default=images)
def filesizes(images):
    """Stat filesize of files.

    Args:
        images: stream of marv image files

    Returns:
        Stream of filesizes
    """
    # Pull each image and push its filesize
    while True:
        img = yield marv.pull(images)
        if img is None:
            break
        yield marv.push(img.size)


@marv.node(Widget)
@marv.input('filesizes', default=filesizes)
def filesize_plot(filesizes):
    # Pull all filesizes
    sizes = []
    while True:
        size = yield marv.pull(filesizes)
        if size is None:
            break
        sizes.append(size)

    # plot
    fig = plt.figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(sizes, 'bo')

    # EE: save figure to file
    plotfile = yield marv.make_file('filesizes.json')
    with open(plotfile.path, 'w') as f:
        json.dump(mpld3.fig_to_dict(fig), f)

    # EE: create plot widget referencing file
    widget = {
        'title': 'Filesizes',
        'mpld3': f'marv-partial:{plotfile.relpath}',
    }

    # Alternative code for community edition:
    # plotfile = yield marv.make_file('filesizes.jpg')
    # fig.savefig(plotfile.path)
    # widget = {
    #     'title': 'Filesizes',
    #     'image': {'src': plotfile.relpath},
    # }

    yield marv.push(widget)


@marv.node(Section)
@marv.input('title', default='Combined')
@marv.input('images', default=images)
@marv.input('filesizes', default=filesizes)
@marv.input('filesize_plot', default=filesize_plot)
def combined_section(title, images, filesizes, filesize_plot):
    # A gallery of images
    imgs = []
    gallery = {'title': images.title, 'gallery': {'images': imgs}}

    # A table with two columns
    rows = []
    columns = [{'title': 'Name', 'formatter': 'rellink'},
               {'title': 'Size', 'formatter': 'filesize'}]
    table = {'table': {'columns': columns, 'rows': rows}}

    # pull images and filesizes synchronously
    while True:
        img, filesize = yield marv.pull_all(images, filesizes)
        if img is None:
            break
        imgs.append({'src': img.relpath})
        rows.append({'cells': [
            {'link': {'href': img.relpath,
                      'title': os.path.basename(img.relpath)}},
            {'uint64': filesize},
        ]})

    # pull filesize_plot AFTER individual messages
    plot = yield marv.pull(filesize_plot)

    # section containing multiple widgets
    section = {'title': title, 'widgets': [table, plot, gallery]}
    yield marv.push(section)


@marv.node(Widget)
@marv.input('filesizes', default=filesizes)
def filesize_plot_fixed(filesizes):
    # set_header() helps marv to schedule nodes
    yield marv.set_header()

    # Pull all filesizes
    sizes = []
    while True:
        size = yield marv.pull(filesizes)
        if size is None:
            break
        sizes.append(size)

    # plot
    fig = plt.figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(sizes, 'bo')
    # axis.set_xlabel('foo')
    # axis.set_ylabel('bat')

    # save figure to file
    plotfile = yield marv.make_file('filesizes.json')
    with open(plotfile.path, 'w') as f:
        json.dump(mpld3.fig_to_dict(fig), f)

    # create plot widget referencing file
    widget = {
        'title': 'Filesizes',
        'mpld3': f'marv-partial:{plotfile.relpath}',
    }
    yield marv.push(widget)


# pylint: disable=invalid-name
combined_section_fixed = combined_section.clone(filesize_plot=filesize_plot_fixed)
