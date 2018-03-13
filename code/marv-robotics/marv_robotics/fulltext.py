# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import marv
from marv.types import Words
from .bag import get_message_type, messages


@marv.node(Words)
@marv.input('stream', foreach=marv.select(messages, '*:std_msgs/String'))
def fulltext_per_topic(stream):
    yield marv.set_header()  # TODO: workaround
    words = set()
    pytype = get_message_type(stream)
    rosmsg = pytype()
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        rosmsg.deserialize(msg.data)
        words.update(rosmsg.data.split())
    if not words:
        raise marv.Abort()
    yield marv.push({'words': list(words)})


@marv.node(Words)
@marv.input('streams', default=fulltext_per_topic)
def fulltext(streams):
    """Extract all text from bag file and store for fulltext search"""
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
    yield marv.push({'words': list(words)})
