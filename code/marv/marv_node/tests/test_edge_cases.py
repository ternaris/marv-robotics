# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import unittest

from ..run import run_nodes
from ..testing import make_dataset, make_sink, marv

dataset = make_dataset()
SETID = dataset.setid


class TestCase(unittest.TestCase):
    def test_foreach_cascade(self):
        @marv.node()
        @marv.input('stream', foreach=[0, 10])
        def images(stream):
            """Produce 2 streams each with two messages"""
            yield marv.set_header(title=stream)
            yield marv.push(1+stream)
            yield marv.push(2+stream)
            yield marv.push(3+stream)
            yield marv.push(4+stream)
            yield marv.push(5+stream)

        @marv.node()
        @marv.input('stream', foreach=images)
        def galleries(stream):
            """Consume each stream into a list"""
            yield marv.set_header(title=stream.title)  # TODO: This is currently needed
            images = []
            while True:
                img = yield marv.pull(stream)
                if img is None:
                    break
                images.append(img)
            yield marv.push({'images': images})

        @marv.node()
        @marv.input('galleries', default=galleries)
        def images_section(galleries):
            """Consume both galleries into a list"""
            tmp = []
            while True:
                msg = yield marv.pull(galleries)
                if msg is None:
                    break
                tmp.append(msg)
            galleries = tmp
            galleries = yield marv.pull_all(*galleries)
            yield marv.push({'galleries': galleries})

        sink = make_sink(images_section)
        run_nodes(dataset, [sink], {})
        self.assertEqual(sink.stream, [{'galleries': [{'images': [1, 2, 3, 4, 5]},
                                                      {'images': [11, 12, 13, 14, 15]}]}])
