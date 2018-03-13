# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import functools
import os
from collections import OrderedDict, deque
from logging import getLogger
from pprint import pformat

from marv_node.setid import SetID
from marv_nodes import dataset as dataset_node
from marv_store.streams import ReadStream

from .driver import Driver
from .event import DefaultOrderedDict
from .io import NEXT, PAUSED, RESUME, THEEND
from .io import Task, MsgRequest
from .stream import Handle, Msg, Stream, VolatileStream


class UnmetDependency(Exception):
    pass


PPINFO = os.environ.get('PPINFO')
MARV_RUN_LOGBREAK = os.environ.get('MARV_RUN_LOGBREAK')
RAISE_IF_UNFINISHED = False


def run_nodes(dataset, nodes, store, persistent=None, force=None,
              deps=None, cachesize=None):

    if cachesize is not None:
        import marv_node
        marv_node.stream.CACHESIZE
        marv_node.stream.CACHESIZE = cachesize

    queue = []
    ret = run_nodes_async(dataset=dataset, nodes=nodes, store=store,
                          queue=queue, persistent=persistent,
                          force=force, deps=deps)
    if ret is None:
        return False

    streams, loop, process_task, after = ret

    # initialize nodes and get initial set of promises
    done = False
    send_queue_empty = False
    while not done:
        # comment while for synchronous
        # while not done and not send_queue_empty:
        #     # additional random break
        #     done, send_queue_empty = process_task(None, None)
        # # random pick from queue
        current, task = queue.pop(0) if queue else (None, None)
        done, send_queue_empty = process_task(current, task)
    after()

    return streams


def run_nodes_async(dataset, nodes, store, queue, persistent=None,
                    force=None, deps=None):
    deps = True if deps is None else deps
    force = False if force is None else force
    assert len(nodes) == len(set(nodes)), nodes
    assert deps in (False, True, 'force'), deps
    assert not any(x.name == 'dataset' for x in nodes)
    persistent = {node: name for name, node in (persistent or {}).items()}
    setid = dataset.setid
    assert isinstance(setid, SetID), setid

    log = getLogger('marv.run')
    logdebug = log.debug
    lognoisy = log.noisy
    logverbose = log.verbose
    loginfo = log.info
    logerror = log.error

    def getname(node):
        return persistent.get(node, node.abbrev)

    drivers = OrderedDict()
    send_queue = deque()

    done = OrderedDict()     # drivers that are finished
    serving = OrderedDict()  # stream.handle -> driver
    streams = OrderedDict()  # stream.handle -> stream
    suspended = []  # suspended drivers
    # {(stream.handle, msg.idx): [driver1, ...]}
    waiting = DefaultOrderedDict(list)
    loggers = OrderedDict()

    def start_driver(driver, force=False):
        assert driver.key not in drivers, driver
        drivers[driver.key] = driver
        send_queue.append((driver, driver.start()))
        store_name = persistent.get(driver.node)

        class LoggerProxy(object):
            def __init__(self, name, prefix):
                self.logger = getLogger(name)
                self.prefix = prefix

            def __getattr__(self, name):
                meth = getattr(self.logger, name)
                @functools.wraps(meth)
                def newmeth(msg, *args, **kw):
                    msg = self.prefix + msg
                    if msg % args == MARV_RUN_LOGBREAK:
                        import ipdb
                        ipdb.set_trace()
                    return meth(msg, *args, **kw)
                return newmeth

        logprefix = '.'.join([setid.abbrev, driver.node.abbrev, driver.name]) + ' '
        logger = LoggerProxy('marv.run', logprefix)
        loggers[driver] = logger
        logmeth = getattr(logger, 'info' if store_name else 'verbose')
        logmeth('%sstarted%s',
                '({}) '.format(store_name) if store_name else '',
                ' with force' if force else '')

    logverbose('evaluating %s %s', setid.abbrev, ' '.join(sorted(getname(x) for x in nodes)))
    for node in sorted(nodes, key=getname):
        handle = Handle(setid=setid, node=node, name='default')
        if handle in store:
            if not force:
                logverbose('skipping stored %s', getname(node))
                continue
        stream = store.create_stream(handle) if node in persistent \
                 else VolatileStream(handle)
        driver = Driver(stream)
        start_driver(driver, force and handle in store)

    if not drivers:
        logverbose('all satisfied.')
        return None

    # TODO: reconsider what pulling means and if needed
    # Drivers for nodes passed to run_nodes and their forks are the
    # ones pulling. Warn if after that there are persistent nodes
    # unfinished and continue until they are finished.
    pulling = OrderedDict((x, None) for x in drivers.values())

    dataset_handle = Handle(setid, dataset_node, 'default')
    streams[dataset_handle] = ReadStream(dataset_handle, None, None,
                                         dataset_node.load(None, dataset))

    def queue_front(driver, send):
        assert driver not in {driver for lst in waiting.values()
                              for driver in lst}
        if driver in suspended:
            suspended.remove(driver)
        assert driver not in suspended
        send_queue.appendleft((driver, send))
        loggers[driver].debug('QUEUE_FRONT %r', send)
        if PPINFO:
            logdebug("state %s", ppinfo())

    def queue_back(driver, send):
        assert driver not in {driver for lst in waiting.values()
                              for driver in lst}
        if driver in suspended:
            suspended.remove(driver)
        assert driver not in suspended
        send_queue.append((driver, send))
        loggers[driver].debug('QUEUE %r', send)
        if PPINFO:
            logdebug("state %s", ppinfo())

    def suspend(driver, _):
        assert driver not in {driver for lst in waiting.values()
                              for driver in lst}
        assert driver not in suspended
        assert driver not in pulling
        suspended.append(driver)
        loggers[driver].debug('SUSPEND')

    def ppinfo():
        lines = ['']
        lines.extend('  ' + x for x in pformat([
            ('drivers', list(drivers.values())),
            ('done', list(done)),
            ('queue', list(queue)),
            ('send_queue', ['{!r} {!r}'.format(x, y) for x, y in send_queue]),
            ('suspended', list(suspended)),
            ('pulling', list(pulling)),
            ('waiting', sorted(['{!r} {!r} {}'.format(driver, handle, idx)
                                for (handle, idx), lst in waiting.items()
                                for driver in lst])),
            ('streams', [(repr(v), v.info()) for k, v in streams.items()]),
        ]).split('\n'))
        return '\n'.join(lines)

    def ppwait():
        return pformat([
            '{} {} {}'.format(driver.key_abbrev, handle.key_abbrev, idx)
            for (handle, idx), lst in waiting.items()
            for driver in lst
        ])
    def pppinfo():
        print(ppinfo())


    class Counter:
        msgnum = 0

    def loop():
        pppinfo  # make available in context for debugging; somebody invented classes...
        if not send_queue:
            # simply wake up all suspended as long as there are
            # unfinished pulling drivers
            if any(driver for lst in waiting.values()
                   for driver in lst
                   if driver in pulling):
                for driver in suspended:
                    queue_back(driver, RESUME)

        if not send_queue:
            return Counter.msgnum == 0, True

        current, send = send_queue.popleft()
        assert current not in {driver for lst in waiting.values()
                               for driver in lst}
        assert current not in suspended
        try:
            if isinstance(send, Msg):
                msg = send
                loggers[current].noisy('<- %s %s',
                                       'HANDLE' if msg.idx == -1 else msg.idx,
                                       msg.handle.key_abbrev)
            else:
                loggers[current].debug('<- %r', send)
            promise = current.send(send)
            assert isinstance(promise, Task), promise
            queue.append((current, promise))
            Counter.msgnum += 1
            #loggers[current].debug('recv %r', promise)
        except StopIteration:
            methname = 'info' if current.node in persistent else 'verbose'
            logmeth = getattr(loggers[current], methname)
            logmeth('finished')
            assert current not in done, current
            done[current] = None

        return False, False

    def process_task(current, task):
        if not (current is None and task is None):
            Counter.msgnum -= 1

        if current is None and task is None:
            return loop()

        logger = loggers[current]

        if task is PAUSED:
            meth = (queue_back if current in pulling else suspend)
            meth(current, RESUME)
            return loop()

        elif isinstance(task, Driver):
            driver = task
            logger.noisy('FORK %s', driver.name)
            start_driver(driver)
            if current in pulling:
                pulling[driver] = None
            queue_back(current, NEXT)
            return loop()

        elif isinstance(task, Stream):
            stream = task
            # TODO: in case of a restart this is ok, see also comment
            # below near reqdriver
            #
            #assert stream.handle not in streams, stream.handle
            #assert stream.handle not in serving
            streams[stream.handle] = stream
            serving[stream.handle] = current
            logger.noisy('ADDSTREAM %s', stream.name)
            queue_front(current, NEXT)
            return loop()

        elif isinstance(task, Msg):
            msg = task
            assert msg.handle.node is current.node
            assert msg.handle.setid == current.setid
            if msg.idx == -1:
                logger.noisy('PUBHANDLE %s', msg.handle.name)
            else:
                logger.noisy('-> %d %s%s',
                             msg.idx,
                             msg.handle.name,
                             ' DONE' if msg.data == THEEND else '')
            stream = streams[msg.handle]
            stream.add_msg(msg)
            waitees = waiting.pop((msg.handle, msg.idx), [])
            for waitee in waitees:
                queue_back(waitee, msg)
            if msg.idx == -1 and stream.parent is not None:
                assert isinstance(msg.data, Handle), msg.data
                msg = stream.parent.handle.msg(msg.data)
                stream.parent.add_msg(msg)
                waitees = waiting.pop((msg.handle, msg.idx), [])
                for waitee in waitees:
                    queue_back(waitee, msg)
            meth = (queue_back if current in pulling else suspend)
            meth(current, NEXT)
            return loop()

        elif isinstance(task, MsgRequest):
            req, (handle, idx) = task, task

            if idx == -1:
                logger.noisy('REQHANDLE %s', handle.key_abbrev)

            # Serve the request
            stream = streams.get(handle)
            forced = False
            if stream is None:
                try:
                    stream = store[handle]
                    if deps == 'force' and handle.node.name != 'dataset' or \
                       force and handle.node in nodes:
                        forced = True
                        stream = None
                    else:
                        logverbose('%r from store', stream)
                        streams[stream.handle] = stream
                except KeyError:
                    if not deps:
                        logerror('%r not in store, running explicitly disabled', handle)
                        raise UnmetDependency()

            try:
                send = stream.get_msg(req) if stream is not None else None
            except IndexError:
                logverbose("state %s", ppinfo())
                logerror('Failed to get %r for %r', req, current)
                raise

            if send is not None:
                queue_back(current, send)
                return loop()

            # Request has to wait
            waitees = waiting[(handle, idx)]
            assert current not in waitees
            waitees.append(current)
            logger.debug('AWAIT %s %s',
                         'HANDLE' if req.idx == -1 else req.idx,
                         req.handle.key_abbrev)

            if handle in serving:
                return loop()

            # Get driver or instantiate it (and request substream)
            node, setid = handle.node, handle.setid
            driver_key = (setid, node, 'default')
            reqdriver = drivers.get(driver_key)
            handles = []
            if reqdriver and handle.name != 'default':
                assert reqdriver.node.group == 'ondemand'
                if not reqdriver.stream_creation:
                    loggers[reqdriver].verbose('restarting')
                    handles = list(reqdriver._requested_streams)
                    reqdriver.destroy()
                    del drivers[reqdriver.key]
                    if reqdriver in done:
                        del done[reqdriver]
                    if reqdriver in suspended:
                        suspended.remove(reqdriver)
                    queue = list(send_queue)
                    send_queue.clear()
                    send_queue.extend(x for x in queue if x[0] != reqdriver)
                    # TODO: If we delete other nodes might request things that don't exist
                    # For now the streams are simply replaced if a
                    # (restarted) driver returns the stream again
                    #
                    # for h, d in serving.items():
                    #     if d == reqdriver:
                    #         del serving[h]
                    #         del streams[h]
                    reqdriver = None
            if reqdriver is None:
                driver_handle = Handle(*driver_key)
                driver_stream = \
                    store.create_stream(driver_handle) if node in persistent else \
                    VolatileStream(driver_handle)
                reqdriver = Driver(driver_stream)
                assert reqdriver.key == driver_key
                start_driver(reqdriver, forced)
                if node in persistent:
                    pulling[reqdriver] = None
            if handle.name != 'default':
                handles.append(handle)
                reqdriver.add_stream_request(*handles)
        else:
            raise RuntimeError('Unknown task: {!r} from {!r}'.format(task, current))

        return loop()

    def after_loop():
        if PPINFO:
            logdebug("state %s", ppinfo())

        # pulling drivers, i.e. those explicitly run, and drivers for
        # persistent nodes must finish.
        unfinished = [(driver.key_abbrev, waitfor) for waitfor, lst in waiting.items()
                      for driver in lst
                      if driver in pulling or driver.node in persistent]

        if unfinished:
            logdebug("state %s", ppinfo())
            logerror('The following nodes did not finish:\n  %s',
                     '\n  '.join('{} waiting for {}'.format(*x) for x in
                                 sorted(unfinished)))
            if RAISE_IF_UNFINISHED:
                assert not unfinished, sorted(unfinished)

    return streams, loop, process_task, after_loop
