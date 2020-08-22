# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from pkg_resources import resource_filename

import marv_api as marv
import marv_node.testing
from marv_node.testing import make_dataset, run_nodes, temporary_directory
from marv_robotics.bag import messages
from marv_store import Store


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
def collect(nooutput, chatter):  # pylint: disable=redefined-outer-name
    msg = yield marv.pull(nooutput)
    assert msg is None
    msg = yield marv.pull(chatter)
    assert msg is not None
    yield marv.push('Success')


class TestCase(marv_node.testing.TestCase):
    # TODO: Generate bags instead, but with connection info!
    BAGS = [resource_filename('marv_node.testing._robotics_tests', 'data/test_0.bag')]

    async def test_node(self):
        with temporary_directory() as storedir:
            store = Store(storedir, {})
            dataset = make_dataset(self.BAGS)
            store.add_dataset(dataset)
            streams = await run_nodes(dataset, [collect], store)
            assert streams == [['Success']]
