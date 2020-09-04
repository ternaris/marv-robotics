# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from unittest import mock

import pytest

from marv.db import Database, DBNotInitialized, DBVersionError
from marv.site import Site


async def test_metadata(tmpdir):
    marv_conf = tmpdir / 'marv.conf'
    marv_conf.write('[marv]\ncollections=')

    # starting without DB must fail
    with pytest.raises(DBNotInitialized):
        site = await Site.create(marv_conf, init=False)

    with mock.patch.object(Database, 'VERSION', '00.01'):
        site = await Site.create(marv_conf, init=True)
        await site.destroy()

        # reusing with same version should work
        site = await Site.create(marv_conf, init=False)
        await site.destroy()

    # reusing with current version must fail
    with pytest.raises(DBVersionError):
        site = await Site.create(marv_conf, init=False)
