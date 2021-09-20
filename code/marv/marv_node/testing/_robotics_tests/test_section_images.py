# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from pkg_resources import resource_filename

import marv_node.testing
from marv_node.testing import make_dataset, run_nodes, temporary_directory
from marv_robotics.cam import images
from marv_robotics.detail import images_section as node
from marv_store import Store

PERSIST = {'images': images}


class TestCase(marv_node.testing.TestCase):
    # TODO: Generate bags instead, but with connection info!
    BAGS = [resource_filename('marv_node.testing._robotics_tests', 'data/cam.bag')]

    async def test_node(self):
        with temporary_directory() as storedir:
            store = Store(storedir, PERSIST)
            dataset = make_dataset(self.BAGS)
            store.add_dataset(dataset)
            streams = await run_nodes(dataset, [node], store, PERSIST)
            self.assertNodeOutput(streams[0], node)
            # TODO: test also header
