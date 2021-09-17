# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: CC0-1.0

import json
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import mpld3
import plotly.graph_objects as go

import marv_api as marv
from marv_detail.types_capnp import Section, Widget  # pylint: disable=no-name-in-module
from marv_nodes.types_capnp import File  # pylint: disable=no-name-in-module
from marv_robotics.bag import make_deserialize, raw_messages
from marv_ros.img_tools import imgmsg_to_cv2

TOPIC = '/wide_stereo/left/image_rect_throttle'

# pylint: disable=redefined-outer-name


@marv.node(File)
@marv.input('cam', marv.select(raw_messages, TOPIC))
def image(cam):
    """Extract first image of input stream to jpg file.

    Args:
        cam: Input stream of raw rosbag messages.

    Yields:
        File instance for first image of input stream.

    """
    # Set output stream title and pull first message
    yield marv.set_header(title=cam.topic)
    msg = yield marv.pull(cam)
    if msg is None:
        return

    # Deserialize raw ros message
    deserialize = make_deserialize(cam)
    rosmsg = deserialize(msg.data)

    # Write image to jpeg and push it to output stream
    name = f"{cam.topic.replace('/', ':')[1:]}.jpg"
    imgfile = yield marv.make_file(name)
    img = imgmsg_to_cv2(rosmsg, 'rgb8')
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

    Yields:
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

    Yields:
        File instances for images of input stream.

    """
    # Set output stream title and pull first message
    yield marv.set_header(title=cam.topic)

    # Fetch and process first 20 image messages
    name_template = f'{cam.topic.replace("/", ":")[1:]}-{{}}.jpg'
    while True:
        idx, msg = yield marv.pull(cam, enumerate=True)
        if msg is None or idx >= 20:
            break

        # Deserialize raw ros message
        deserialize = make_deserialize(cam)
        rosmsg = deserialize(msg.data)

        # Write image to jpeg and push it to output stream
        img = imgmsg_to_cv2(rosmsg, 'rgb8')
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

    Yields:
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

    Yields:
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

    # plot with plotly
    fig = go.Figure(data=go.Scatter(y=sizes))

    # save plotly figure to file
    plotfile = yield marv.make_file('filesizes_plotly.json')
    Path(plotfile.path).write_text(fig.to_json())

    # create plotly widget referencing file
    widget_plotly = {
        'title': 'Filesizes (plotly)',
        'plotly': f'marv-partial:{plotfile.relpath}',
    }

    # plot with matplotlib
    fig = plt.figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.plot(sizes, 'bo')

    # save mpld3 figure to file
    plotfile = yield marv.make_file('filesizes_mpld3.json')
    Path(plotfile.path).write_text(json.dumps(mpld3.fig_to_dict(fig)))

    # create mpld3 plot widget referencing file
    widget_mpld3 = {
        'title': 'Filesizes (mpld3)',
        'mpld3': f'marv-partial:{plotfile.relpath}',
    }

    # save plot as image
    plotfile = yield marv.make_file('filesizes.jpg')
    fig.savefig(plotfile.path)

    # create image widget referencing file
    widget_image = {
        'title': 'Filesizes (image)',
        'image': {
            'src': plotfile.relpath,
        },
    }

    # Let the user choose which widget to show with a dropdown
    yield marv.push(
        {
            'title': 'Filesize plots',
            'dropdown': {
                'widgets': [
                    widget_plotly,
                    widget_mpld3,
                    widget_image,
                ],
            },
        },
    )


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
    columns = [
        {
            'title': 'Name',
            'formatter': 'rellink',
            'sortkey': 'title',
        },
        {
            'title': 'Size',
            'formatter': 'filesize',
        },
    ]
    table = {'table': {'columns': columns, 'rows': rows}}

    # pull images and filesizes synchronously
    while True:
        img, filesize = yield marv.pull_all(images, filesizes)
        if img is None:
            break
        imgs.append({'src': img.relpath})
        rows.append(
            {
                'cells': [
                    {
                        'link': {
                            'href': img.relpath,
                            'title': Path(img.relpath).name,
                        },
                    },
                    {
                        'uint64': filesize,
                    },
                ],
            },
        )

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
    with open(plotfile.path, 'w', encoding='utf-8') as f:
        json.dump(mpld3.fig_to_dict(fig), f)

    # create plot widget referencing file
    widget = {
        'title': 'Filesizes',
        'mpld3': f'marv-partial:{plotfile.relpath}',
    }
    yield marv.push(widget)


# pylint: disable=invalid-name
combined_section_fixed = combined_section.clone(filesize_plot=filesize_plot_fixed)
