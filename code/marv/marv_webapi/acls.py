# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division

"""Access control lists

Use access control lists (ACLs) to control who can perform which
actions. An ACL is a function that returns a dictionary mapping route
function names to list of groups being allowed to access the
route. The special groups ``__authenticated__`` and
``__unauthenticated__`` are automatically assigned within
authenticated, resp. unauthenticated sessions.

"""

def authenticated():
    """Require authentication

    - require authentication for everything
    - only admins may delete datasets
    """
    return {
        'collection': ['__authenticated__'],
        'comment': ['__authenticated__'],
        'compare': ['__authenticated__'],
        'delete': ['admin'],
        'detail': ['__authenticated__'],
        'file_list': ['__authenticated__'],
        'get_partial_url': ['__authenticated__'],
        'get_stream_url': ['__authenticated__'],
        'stream': ['__authenticated__'],
        'tag': ['__authenticated__'],
    }


def public():
    """Allow public access

    - anyone can read anything
    - authenticated users can comment, tag and compare
    - only admins may delete datasets
    """
    return {
        'collection': ['__unauthenticated__', '__authenticated__'],
        'comment': ['__authenticated__'],
        'compare': ['__authenticated__'],
        'delete': ['admin'],
        'detail': ['__unauthenticated__', '__authenticated__'],
        'file_list': ['__unauthenticated__', '__authenticated__'],
        'get_partial_url': ['__unauthenticated__', '__authenticated__'],
        'get_stream_url': ['__unauthenticated__', '__authenticated__'],
        'stream': ['__unauthenticated__'],
        'tag': ['__authenticated__'],
    }
