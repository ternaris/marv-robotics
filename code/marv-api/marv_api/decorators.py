# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from marv_node.node import StreamSpec, input, node


# NOTE: Strictly speaking not a decorator but related to decoration of node functions
def select(node, name):  # pylint: disable=redefined-outer-name
    """Select specific stream of a node by name.

    Args:
        node: A node producing a group of streams.
        name (str): Name of stream to select.

    Returns:
        Node outputting selected stream.

    """
    return StreamSpec(node, name)


__all__ = (
    'input',
    'node',
    'select',
)
