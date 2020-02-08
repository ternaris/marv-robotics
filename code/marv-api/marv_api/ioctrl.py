# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from .iomsgs import (CreateStream, GetLogger, GetRequested, Handle, MakeFile, Pull, PullAll, Push,
                     SetHeader)


class Abort(Exception):
    pass


def create_stream(name, **header):
    """Create a stream for publishing messages.

    All keyword arguments will be used to form the header.
    """
    assert isinstance(name, str), name
    return CreateStream(parent=None, name=name, group=False, header=header)


def create_group(name, **header):
    assert isinstance(name, str), name
    return CreateStream(parent=None, name=name, group=True, header=header)


def get_logger():
    return GetLogger()


def get_requested():
    return GetRequested()


def make_file(name):
    assert isinstance(name, str)
    return MakeFile(None, name)


def pull(handle, enumerate=False):
    """Pull next message for handle.

    Args:
        handle: A :class:`.stream.Handle` or GroupHandle.
        enumerate (bool): boolean to indicate whether a tuple ``(idx, msg)``
            should be returned, not unlike Python's enumerate().

    Returns:
        A :class:`Pull` task to be yielded. Marv will send the
        corresponding message as soon as it is available. For groups
        this message will be a handle to a member of the
        group. Members of groups are either streams or groups.

    Examples:
        Pulling (enumerated) message from stream::

            msg = yield marv.pull(stream)
            idx, msg = yield marv.pull(stream, enumerate=True)

        Pulling stream from group and message from stream::

            stream = yield marv.pull(group)  # a group of streams
            msg = yield marv.pull(stream)

    """
    assert isinstance(handle, Handle), handle
    return Pull(handle, enumerate)


def pull_all(*handles):
    """Pull next message of all handles."""
    return PullAll(handles)


def push(msg):
    return Push(msg)


def set_header(**header):
    """Set the header of a stream or group."""
    # If a node is configured to have a header, the header needs to be
    # set before yielding any messages or creating group members. Once a
    # header is set, a handle is created and dependent nodes can be
    # instantiated. For streams without headers this happens right away.
    #
    #     @marv.node(header=True)
    #     def node():
    #         yield marv.set_header(title='Title')
    #
    # """
    return SetHeader(header)
