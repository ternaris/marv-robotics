# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

"""Dataset scanner.

Datasets are created based on information provided by scanners.  A
scanner is responsible to group files into named datasets::

    from marv_api import DatasetInfo

    def scan(dirpath, dirnames, filenames):
        return [DatasetInfo(os.path.basename(x), [x])
                for x in filenames
                if x.endswith('.csv')]

Scanners are called for every directory within the configured
scanroots, while files and directories starting with a ``.`` and
directories containing an (empty) ``.marvignore`` file are ignored and
will not be traversed into.

Further, traversal into subdirectories can be controlled by
altering the :paramref:`.dirnames` list in-place. To block further
traversal, e.g. for a directory-based dataset type, set it to an
empty list -- :py:func:`os.walk` is used behind the scenes::

  dirnames[:] = []

"""

from collections import namedtuple

DatasetInfo = namedtuple('DatasetInfo', ('name', 'files'))
