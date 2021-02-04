# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import sysconfig
from configparser import ConfigParser
from pathlib import Path

import pytest

from marv import config
from marv.config import ConfigError

CONFIG = """
[marv]
reverse_proxy =

  nginx

collections =
   # comment
   foo

  bar

[collection foo]
scanner =

  marv_robotics.bag:scan

scanroots =
    ../foo

      bar
  /absolute

[collection bar]
scanner = marv_robotics.bag:scan
scanroots = foo
"""

COLMISSING = """
[marv]
collections = foo bar

[collections bar]
scanner = foo
scanroots = foo
"""

COLUNMENTIONED = """
[marv]
collections = foo

[collections foo]
scanner = foo
scanroots = foo

[collections bar]
scanner = foo
scanroots = foo
"""


def parse(path, string):
    parser = ConfigParser()
    parser.read_string(string, str(path))
    return config.Config.from_parser(path, parser)


def test_config():
    cfg = parse('site/marv.conf', CONFIG)
    configpath = Path('site/marv.conf').resolve()
    sitedir = configpath.parent
    assert cfg.filename == configpath
    assert cfg.marv.sitedir == sitedir
    assert cfg.marv.collections == ('foo', 'bar')
    assert cfg.marv.dburi == f'sqlite://{sitedir}/db/db.sqlite'
    assert cfg.marv.frontenddir == sitedir / 'frontend'
    assert cfg.marv.reverse_proxy == 'nginx'
    assert cfg.marv.sessionkey_file == sitedir / 'sessionkey'
    assert cfg.marv.staticdir.is_absolute()
    assert cfg.marv.storedir == sitedir / 'store'
    assert cfg.marv.upload_checkpoint_commands == ()
    assert cfg.marv.venv == sitedir / 'venv'
    assert cfg.marv.sitepackages == sitedir / 'venv' / 'lib' / \
        f'python{sysconfig.get_python_version()}' / 'site-packages'

    assert cfg.collections.keys() == {'foo', 'bar'}
    colcfg = cfg.collections['foo']
    assert colcfg.sitedir == sitedir
    assert colcfg.scanner == 'marv_robotics.bag:scan'
    assert colcfg.scanroots == (sitedir.parent / 'foo',
                                sitedir / 'bar',
                                Path('/absolute'))


def test_marv_collections():
    parse('site/marv.conf', COLUNMENTIONED)
    with pytest.raises(ConfigError) as einfo:
        parse('site/marv.conf', COLMISSING)
    assert "could not be parsed for ['foo']" in str(einfo.value)


def test_validators():
    assert config.resolve_path(None) is None
    assert config.resolve_path('foo') == Path('foo').resolve()
    assert config.resolve_relto_site(None, {}) is None
    assert config.resolve_relto_site('foo', {'sitedir': Path('/site')}) == Path('/site/foo')
    assert config.split(None) == []
    assert config.split('\n a\n  b ') == ['a', 'b']
    assert config.splitlines(None) == []
    assert config.splitlines('\n  foo bar  \n\nbaz') == ['foo bar', 'baz']
    assert config.splitlines_relto_site(None, {}) == []
    assert config.splitlines_relto_site('\n../foo\n  bar', {'sitedir': Path('/site')}) == \
        [Path('/foo'), Path('/site/bar')]
    assert config.splitlines_split(None) == []
    assert config.splitlines_split('\n  foo bar  \n\nbaz') == [['foo', 'bar'], ['baz']]
    assert config.splitpipe(None) == []
    assert config.splitpipe(' foo | bar ') == ['foo', 'bar']
    assert config.strip(None) is None
    assert config.strip('   foo bar \n') == 'foo bar'  # noqa: B005

    # pylint: disable=no-value-for-parameter
    with pytest.raises(ValueError):
        assert config.MarvConfig.dburi_relto_site(None, None)
    with pytest.raises(ValueError):
        assert config.MarvConfig.dburi_relto_site(None, 'foo')
    assert config.MarvConfig.dburi_relto_site('sqlite:///foo', None) == 'sqlite:///foo'
    assert config.MarvConfig.dburi_relto_site('sqlite://../foo', {'sitedir': Path('/site')}) == \
        'sqlite:///foo'
    assert config.MarvConfig.oauth_split(None) == {}
    assert config.MarvConfig.oauth_split('\nfoo | foo1 | foo2\n\n  bar | bar1 | bar2\n\n') == {
        'foo': ['foo', 'foo1', 'foo2'],
        'bar': ['bar', 'bar1', 'bar2'],
    }
    # pylint: enable=no-value-for-parameter

# TODO: mismatch collections = and [collections]
