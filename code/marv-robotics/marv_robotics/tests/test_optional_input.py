# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import marv
import marv_node.testing
from marv_node.testing import make_dataset, make_sink, run_nodes, temporary_directory
from marv_store import Store
from pkg_resources import resource_filename

from marv_robotics.bag import messages


@marv.node()
@marv.input('stream', default=marv.select(messages, '/non-existent'))
def nooutput(stream):
    yield marv.set_header()
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            return
        yield marv.push(msg)


@marv.node()
@marv.input('nooutput', default=nooutput)
@marv.input('chatter', default=marv.select(messages, '/chatter'))
def collect(nooutput, chatter):
    msg = yield marv.pull(nooutput)
    assert msg is None
    msg = yield marv.pull(chatter)
    assert msg is not None
    yield marv.push('Success')


class TestCase(marv_node.testing.TestCase):
    # TODO: Generate bags instead, but with connection info!
    BAGS = [resource_filename('marv_robotics.tests', 'data/test_0.bag')]

    def test_node(self):
        with temporary_directory() as storedir:
            store = Store(storedir, {})
            dataset = make_dataset(self.BAGS)
            store.add_dataset(dataset)
            sink = make_sink(collect)
            run_nodes(dataset, [sink], store)
            self.assertEquals(sink.stream, ['Success'])
