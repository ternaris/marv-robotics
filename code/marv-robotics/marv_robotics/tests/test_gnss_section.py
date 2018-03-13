# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import marv_node.testing
from marv_node.testing import make_dataset, make_sink, run_nodes, temporary_directory
from marv_nodes import SetID
from marv_store import Store
from pkg_resources import resource_filename

from marv_robotics.detail import gnss_section as node
from marv_robotics.gnss import gnss_plots


PERSIST = {gnss_plots.name: gnss_plots}


class TestCase(marv_node.testing.TestCase):
    # TODO: Generate bags instead, but with connection info!
    BAGS = [resource_filename('marv_robotics.tests', 'data/cam.bag')]

    def test_node(self):
        with temporary_directory() as storedir:
            store = Store(storedir, PERSIST)
            dataset = make_dataset(self.BAGS)
            store.add_dataset(dataset)
            sink = make_sink(node)
            run_nodes(dataset, [sink], store, PERSIST)
            self.assertNodeOutput(sink.stream, node)
            # XXX: test also header
