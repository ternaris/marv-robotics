# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import re

import marv_api as marv
from marv_api.types import Words

from .bag import make_deserialize, messages

WSNULL = re.compile(r'[\s\x00]')


@marv.node(Words)
@marv.input('stream', foreach=marv.select(messages, ('*:std_msgs/String,'
                                                     '*:std_msgs/msg/String')))
def fulltext_per_topic(stream):
    yield marv.set_header(title=stream.topic)
    words = set()
    deserialize = make_deserialize(stream)
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        rosmsg = deserialize(msg.data)
        words.update(WSNULL.split(rosmsg.data))

    if not words:
        raise marv.Abort()
    yield marv.push({'words': list(words)})


@marv.node(Words)
@marv.input('streams', default=fulltext_per_topic)
def fulltext(streams):
    """Extract all text from bag file and store for fulltext search."""
    tmp = []
    while True:
        stream = yield marv.pull(streams)
        if stream is None:
            break
        tmp.append(stream)
    streams = tmp
    if not streams:
        raise marv.Abort()

    msgs = yield marv.pull_all(*streams)
    words = {x for msg in msgs for x in msg.words}
    yield marv.push({'words': sorted(words)})
