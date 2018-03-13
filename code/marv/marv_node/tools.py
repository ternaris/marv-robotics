# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

from marv_node.node import StreamSpec as _StreamSpec


def select(node, name):
    """Select specific stream of a node by name.

    Args:
        node: A node producing a group of streams.
        name (str): Name of stream to select.

    Returns:
        Node outputting selected stream.
    """
    return _StreamSpec(node, name)
