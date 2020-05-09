# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

import pytest
from aiohttp import web

from marv_webapi.tooling import safejoin


def test_safejoin():
    with pytest.raises(web.HTTPForbidden):
        safejoin(Path('/base'), Path('/foo'))

    with pytest.raises(web.HTTPForbidden):
        safejoin(Path('/base'), Path('../foo'))

    with pytest.raises(web.HTTPForbidden):
        safejoin(Path('/base'), Path('foo/../../bar'))

    assert str(safejoin(Path('/base'), Path('foo//bar'))) == '/base/foo/bar'
