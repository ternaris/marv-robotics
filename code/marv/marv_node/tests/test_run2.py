# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import unittest
from collections import defaultdict
from itertools import product

from ..testing import make_dataset, make_sink, marv

from ..run import run_nodes
from ..stream import Handle


dataset = make_dataset()
SETID = dataset.setid


class TestCase(unittest.TestCase):
    def test_plain_is_error(self):
        @marv.node()
        def source():
            yield 1

        sink = make_sink(source)
        with self.assertRaises(RuntimeError):  # TODO: propert exc
            run_nodes(dataset, [sink], {})

    def test_one_source(self):
        @marv.node()
        def source():
            yield marv.push(1)
            yield marv.push(2)
            yield marv.push(3)

        sink = make_sink(source)
        run_nodes(dataset, [sink], {})
        self.assertEqual(sink.stream, [1, 2, 3])

    def test_one_consumer(self):
        @marv.node()
        def source():
            yield marv.push(1)
            yield marv.push(2)
            yield marv.push(3)

        @marv.node()
        def cubic():
            stream = yield marv.get_stream(source)
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                yield marv.push(msg**3)

        sink = make_sink(cubic)
        run_nodes(dataset, [sink], {})
        self.assertEqual(sink.stream, [1, 8, 27])

    def test_two_consumers(self):
        @marv.node()
        def source():
            yield marv.push(1)
            yield marv.push(2)
            yield marv.push(3)

        @marv.node()
        def cubic():
            stream = yield marv.get_stream(source)
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                msg = yield marv.push(msg**3)

        source_sink = make_sink(source)
        cubic_sink = make_sink(cubic)
        run_nodes(dataset, [source_sink, cubic_sink], {})
        self.assertEqual(source_sink.stream, [1, 2, 3])
        self.assertEqual(cubic_sink.stream, [1, 8, 27])

    def test_ondemand_group(self):
        @marv.node(group='ondemand')
        def source():
            requested = yield marv.get_requested()
            self.assertIn(Handle(SETID, source, 'evensub'), requested)
            self.assertIn(Handle(SETID, source, 'oddsub'), requested)
            self.assertIn(Handle(SETID, source, 'primesub'), requested)

            out = {x.name: marv.create_stream(x.name) for x in requested}
            for k, stream in out.items():
                out[k] = yield stream
            self.assertEqual(sorted(out.keys()), ['evensub', 'oddsub', 'primesub'])

            for i in range(1, 6):
                yield marv.push(out['oddsub' if i % 2 else 'evensub'].msg(i))
                if i in [2, 3, 5]:
                    yield marv.push(out['primesub'].msg(i))

            # How do we output one message for multiple streams?

        @marv.node()
        def even():
            stream = yield marv.get_stream(source, 'evensub')
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                msg = yield marv.push(msg)

        @marv.node()
        def odd():
            stream = yield marv.get_stream(source, 'oddsub')
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                msg = yield marv.push(msg)

        @marv.node()
        def prime():
            stream = yield marv.get_stream(source, 'primesub')
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                msg = yield marv.push(msg)

        even_sink = make_sink(even)
        odd_sink = make_sink(odd)
        prime_sink = make_sink(prime)
        run_nodes(dataset, [even_sink, odd_sink, prime_sink], {})
        self.assertEqual(even_sink.stream, [2, 4])
        self.assertEqual(odd_sink.stream, [1, 3, 5])
        self.assertEqual(prime_sink.stream, [2, 3, 5])

    def test_ondemand_group_with_restart(self):
        reqs = []
        @marv.node(group='ondemand')
        def source():
            requested = yield marv.get_requested()
            reqs.append(requested)
            creates = [marv.create_stream(x.name) for x in requested]
            streams = []
            for create in creates:
                stream = yield create
                streams.append(stream)
            msgs = list(product(streams, [1, 2]))
            for stream, msg in msgs:
                yield marv.push(stream.msg(msg))

        msgs = []
        @marv.node()
        def consumer():
            stream1 = yield marv.get_stream(source, 'a')
            stream2 = yield marv.get_stream(source, 'b')
            streams = [stream1, stream2]
            while streams:
                for stream in streams[:]:
                    msg = yield marv.pull(stream)
                    if msg is None:
                        streams.remove(stream)
                        continue
                    msgs.append((stream.name, msg))

        run_nodes(dataset, [consumer], {})
        self.assertEqual(reqs, [
            [Handle(SETID, source, 'a')],
            [Handle(SETID, source, 'a'), Handle(SETID, source, 'b')],
        ])
        self.assertEqual(msgs, [('a', 1), ('b', 1), ('a', 2), ('b', 2)])

    def test_ondemand_group_with_restart_and_foreach(self):
        reqs = []
        @marv.node(group='ondemand')
        def source():
            requested = yield marv.get_requested()
            reqs.append(requested)
            creates = [marv.create_stream(x.name) for x in requested]
            streams = []
            for create in creates:
                stream = yield create
                streams.append(stream)
            msgs = list(product(streams, [1,2]))
            for stream, msg in msgs:
                yield marv.push(stream.msg(msg))

        @marv.node()
        def streamA():
            stream = yield marv.get_stream(source, 'a')
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                msg = yield marv.push(msg)

        @marv.node()
        def streamB():
            stream = yield marv.get_stream(source, 'b')
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                msg = yield marv.push(msg)

        @marv.node(group=True)
        def merged():
            stream1 = yield marv.get_stream(streamA)
            stream2 = yield marv.get_stream(streamB)
            yield marv.push(stream1)
            yield marv.push(stream2)

        msgs = []
        @marv.node()
        @marv.input('stream', foreach=merged)
        def consumer(stream):
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                msgs.append((stream, msg))

        run_nodes(dataset, [consumer], {})
        self.maxDiff = None
        self.assertEqual(reqs, [[Handle(SETID, source, 'a')],
                                [Handle(SETID, source, 'a'), Handle(SETID, source, 'b')]])
        self.assertEqual(msgs, [(Handle(SETID, streamA, 'default'), 1),
                                (Handle(SETID, streamA, 'default'), 2),
                                (Handle(SETID, streamB, 'default'), 1),
                                (Handle(SETID, streamB, 'default'), 2)])

    def test_request_input(self):
        started = defaultdict(bool)
        finished = defaultdict(bool)

        @marv.node(group=True)
        def multi():
            started[multi] = True
            a_out = yield marv.create_stream('a')
            b_out = yield marv.create_stream('b')
            self.assertEqual(a_out, Handle(SETID, multi, 'a'))
            self.assertEqual(b_out, Handle(SETID, multi, 'b'))

            yield a_out.msg(1)
            yield b_out.msg(10)
            yield a_out.msg(2)
            yield b_out.msg(20)
            finished[multi] = True

        @marv.node()
        def consumer():
            started[consumer] = True
            node = yield marv.get_stream(multi)
            a_in, b_in = yield marv.pull_all(node, node)
            self.assertEqual(a_in, Handle(SETID, multi, 'a'))
            self.assertEqual(b_in, Handle(SETID, multi, 'b'))
            # streams = yield marv.io(*node)  # like for values
            # streams = yield marv.io(node, consume=True)  # a bit less voodoo

            values = []
            while True:
                msgs = yield marv.pull_all(a_in, b_in)
                if msgs == [None, None]:
                    break
                values.append(msgs)
            self.assertEqual(values, [[1, 10], [2, 20]])
            finished[consumer] = True

        run_nodes(dataset, [consumer], {})
        self.assertTrue(started[multi])
        self.assertTrue(started[consumer])
        self.assertTrue(finished[multi])
        self.assertTrue(finished[consumer])

    def test_fork(self):
        @marv.node(group=True)
        def source():
            out1 = yield marv.create_stream('Output 1')
            out2 = yield marv.create_stream('Output 2')
            out3 = yield marv.create_stream('Output 3')
            yield out1.msg(a=1)
            yield out2.msg(b=10)
            yield out3.msg(c=100)
            yield out1.msg(a=2)
            yield out2.msg(b=20)
            yield out3.msg(c=200)

        foreach_msgs = defaultdict(list)

        @marv.node(group=True)
        def forking(stream=None):
            node = yield marv.get_stream(source)  # UX not nice, naming

            if stream is None:
                stream = yield marv.pull(node)
                other = yield marv.pull(node)
                while other is not None:
                    name = other.key[-1]
                    yield marv.fork(name, inputs={'stream': other}, group=False)
                    other = yield marv.pull(node)

            msgs = foreach_msgs[stream.key]
            msg = yield marv.pull(stream)
            while msg:
                msgs.append(msg)
                msg = yield marv.pull(stream)

        run_nodes(dataset, [forking], {})
        self.assertEqual(dict(foreach_msgs), {
            (SETID, source, 'Output 1'): [{'a': 1}, {'a': 2}],
            (SETID, source, 'Output 2'): [{'b': 10}, {'b': 20}],
            (SETID, source, 'Output 3'): [{'c': 100}, {'c': 200}],
        })

    def test_foreach(self):
        @marv.node(group=True)
        def source():
            out1 = yield marv.create_stream('Output 1', foo=1)
            out2 = yield marv.create_stream('Output 2', foo=2)
            out3 = yield marv.create_stream('Output 3', foo=3)
            yield out1.msg(a=1)
            yield out2.msg(b=10)
            yield out3.msg(c=100)
            yield out1.msg(a=2)
            yield out2.msg(b=20)
            yield out3.msg(c=200)

        foreach_msgs = defaultdict(list)
        @marv.node()
        @marv.input('stream', foreach=source)
        def foreach(stream):
            assert stream.key not in foreach_msgs
            msgs = foreach_msgs[stream.key]
            msg = yield marv.pull(stream)
            while msg:
                msgs.append(msg)
                msg = yield marv.pull(stream)

        streams = []
        all_msgs = []
        @marv.node()
        @marv.input('node', default=source)
        def withall(node):
            while True:
                stream = yield marv.pull(node)
                if stream is None:
                    break
                streams.append(stream)

            msgs = yield marv.pull_all(*streams)
            while filter(None, msgs):
                all_msgs.append(msgs)
                msgs = yield marv.pull_all(*streams)

        run_nodes(dataset, [foreach, withall], {})
        self.assertEqual(streams, [Handle(SETID, source, 'Output 1'),
                                   Handle(SETID, source, 'Output 2'),
                                   Handle(SETID, source, 'Output 3')])
        self.assertEqual(streams[0].header['foo'], 1)
        self.assertEqual(streams[1].header['foo'], 2)
        self.assertEqual(streams[2].header['foo'], 3)
        self.assertEqual(all_msgs, [[{'a': 1}, {'b': 10}, {'c': 100}],
                                    [{'a': 2}, {'b': 20}, {'c': 200}]])
        self.maxDiff = None
        self.assertEqual(dict(foreach_msgs), {
            (SETID, source, 'Output 1'): [{'a': 1}, {'a': 2}],
            (SETID, source, 'Output 2'): [{'b': 10}, {'b': 20}],
            (SETID, source, 'Output 3'): [{'c': 100}, {'c': 200}],
        })

    def test_foreach_with_header(self):
        @marv.node(group=True)
        def source():
            out1 = yield marv.create_stream('Output 1', foo=1)
            yield out1.msg(a=1)
            yield out1.msg(a=2)

        @marv.node()
        @marv.input('stream', foreach=source)
        def foreach(stream):
            yield marv.set_header(**stream.header)
            while True:
                msg = yield marv.pull(stream)
                if msg is None:
                    break
                msg = yield marv.push(msg)

        foreach_msgs = defaultdict(list)
        foreach_streams = []
        @marv.node()
        @marv.input('foreaches', default=foreach)
        def consumer(foreaches):
            while True:
                stream = yield marv.pull(foreaches)
                if stream is None:
                    break
                foreach_streams.append(stream)
                msgs = foreach_msgs[stream.key]
                while True:
                    msg = yield marv.pull(stream)
                    if msg is None:
                        break
                    msgs.append(msg)

        run_nodes(dataset, [consumer], {})
        self.assertEqual(len(foreach_streams), 1)
        handle = foreach_streams[0]
        self.assertEqual(handle, Handle(SETID, foreach, '0'))
        self.assertEqual(handle.foo, 1)
        self.maxDiff = None
        self.assertEqual(dict(foreach_msgs), {
            (SETID, foreach, '0'): [{'a': 1}, {'a': 2}],
        })

    def test_create_stream(self):
        @marv.node(group=True)
        def source():
            out1 = yield marv.create_stream('Output 1')
            out2 = yield marv.create_stream('Output 2', foo=1)

        handles = []
        @marv.node()
        @marv.input('source', source)
        def consumer(source):
            stream = yield marv.pull(source)
            handles.append(stream)
            stream = yield marv.pull(source)
            handles.append(stream)

        run_nodes(dataset, [consumer], {})
        self.assertEqual(handles[0].name, 'Output 1')
        self.assertEqual(handles[1].name, 'Output 2')
        self.assertEqual(handles[1].foo, 1)
        with self.assertRaises(AttributeError):
            handles[0].foo
