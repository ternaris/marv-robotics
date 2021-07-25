# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import pickle
from pathlib import Path

import capnp  # pylint: disable=unused-import
import pytest

from marv_api.types import File
from marv_nodes import Dataset
from marv_pycapnp import Wrapper

from .test_wrapper_capnp import TestStruct  # pylint: disable=import-error


def test():
    # pylint: disable=too-many-statements
    builder = TestStruct.new_message()
    reader = builder.as_reader()
    wrapper = Wrapper(reader, streamdir=None, setdir=None)
    assert repr(wrapper) == '<Wrapper marv_pycapnp.tests.test_wrapper_capnp:TestStruct>'

    builder.text = '\u03a8'
    assert wrapper.text == '\u03a8'
    assert isinstance(wrapper.text, str)

    builder.data = '\u03a8'.encode()
    assert wrapper.data == '\u03a8'.encode()
    assert isinstance(wrapper.data, bytes)

    builder.textList = ['\u03a8']
    assert wrapper.text_list == ['\u03a8']
    assert wrapper.text_list[:] == ['\u03a8']
    assert list(wrapper.text_list) == ['\u03a8']
    assert isinstance(wrapper.text_list[0], str)
    assert repr(wrapper.textList) == "['Ψ']"

    builder.dataList = ['\u03a8'.encode()]
    assert wrapper.data_list == ['\u03a8'.encode()]
    assert wrapper.data_list[:] == ['\u03a8'.encode()]
    assert list(wrapper.data_list) == ['\u03a8'.encode()]
    assert isinstance(wrapper.data_list[0], bytes)
    assert repr(wrapper.dataList) == "[b'\\xce\\xa8']"

    builder.textListInList = [[u'\u03a8'], [u'\u03a8']]
    builder.dataListInList = [[u'\u03a8'.encode()], [u'\u03a8'.encode()]]
    assert all(isinstance(x, str) for lst in wrapper.textListInList for x in lst)
    assert all(isinstance(x, bytes) for lst in wrapper.dataListInList for x in lst)

    nested = Wrapper.from_dict(
        schema=TestStruct,
        data={
            'text': '\u03a8',
            'data': '\u03a8'.encode(),
            'textList': ['\u03a8'],
            'dataList': ['\u03a8'.encode()],
            'textListInList': [['\u03a8'], [u'\u03a8']],
            'dataListInList': [['\u03a8'.encode()], ['\u03a8'.encode()]],
        },
    )
    builder.nestedList = [nested._reader]  # pylint: disable=protected-access
    assert isinstance(wrapper.nested_list[0].text, str)
    assert isinstance(wrapper.nested_list[0].data, bytes)
    assert isinstance(wrapper.nested_list[0].textList[0], str)
    assert isinstance(wrapper.nested_list[0].dataList[0], bytes)

    builder.unionData = '\u03a8'.encode()
    assert isinstance(wrapper.union_data, bytes)

    builder.unionText = '\u03a8'
    assert isinstance(wrapper.union_text, str)

    builder.union.data = '\u03a8'.encode()
    assert isinstance(wrapper.union.data, bytes)

    builder.union.text = '\u03a8'
    assert isinstance(wrapper.union.text, str)

    builder.group.text = '\u03a8'
    assert isinstance(wrapper.group.text, str)

    builder.group.data = '\u03a8'.encode()
    assert isinstance(wrapper.group.data, bytes)

    builder.enum = 'foo'
    assert wrapper.enum == 'foo'

    builder.enum = 'bar'
    assert wrapper.enum == 'bar'

    dct = wrapper.to_dict(which=True)
    assert dct == {
        'data': b'\xce\xa8',
        'dataList': [b'\xce\xa8'],
        'dataListInList': [[b'\xce\xa8'], [b'\xce\xa8']],
        'enum': 'bar',
        'group': {
            'data': b'\xce\xa8',
            'text': '\u03a8',
        },
        'nestedList': [
            {
                'data': b'\xce\xa8',
                'dataList': [b'\xce\xa8'],
                'dataListInList': [[b'\xce\xa8'], [b'\xce\xa8']],
                'enum': 'foo',
                'group': {
                    'data': b'',
                    'text': '',
                },
                'nestedList': [],
                'text': '\u03a8',
                'textList': ['\u03a8'],
                'textListInList': [['\u03a8'], ['\u03a8']],
                'union': {
                    'text': '',
                    '_which': 'text',
                },
                'unionText': '',
                '_which': 'unionText',
            },
        ],
        'text': '\u03a8',
        'textList': ['\u03a8'],
        'textListInList': [['\u03a8'], ['\u03a8']],
        'union': {
            'text': '\u03a8',
            '_which': 'text',
        },
        'unionText': '\u03a8',
        '_which': 'unionText',
    }

    # dict rountrip
    dct = wrapper.to_dict()
    roundtrip = Wrapper.from_dict(TestStruct, dct)
    assert dct == roundtrip.to_dict()

    # pickle roundtrip
    data = pickle.dumps(wrapper, protocol=5)
    roundtrip = pickle.loads(data)
    assert wrapper.to_dict() == roundtrip.to_dict()

    with pytest.raises(RuntimeError):
        data = pickle.dumps(wrapper)


def test_file_wrapper():
    wrapper = Wrapper.from_dict(TestStruct, {})
    with pytest.raises(AttributeError):
        assert wrapper.path
    with pytest.raises(AttributeError):
        assert wrapper.relpath

    wrapper = Wrapper.from_dict(File, {'path': '/foo'}, setdir=Path(__file__).parent.parent)
    assert wrapper.path == '/foo'
    with pytest.raises(AttributeError):
        assert wrapper.relpath

    wrapper = Wrapper.from_dict(File, {'path': __file__},
                                setdir=Path(__file__).parent.parent,
                                streamdir=Path(__file__).parent)
    assert wrapper.path == __file__

    wrapper = Wrapper.from_dict(File, {'path': '/path/to/setdir/streamdir/file'},
                                setdir='/path/to/moved/setdir', streamdir='/irrelevant')
    assert wrapper.path == '/path/to/moved/setdir/streamdir/file'

    wrapper = Wrapper.from_dict(File, {'path': '/path/to/setdir/.streamdir/file'},
                                setdir='/path/to/moved/setdir', streamdir='/irrelevant')
    assert wrapper.path == '/path/to/moved/setdir/streamdir/file'
    assert wrapper.relpath == 'streamdir/file'

    # Moved, but old path exists, i.e. copied
    # Rhe last component of setdir is the setid, which usually is a random hash and looked for
    # in the stored path to return the new path.
    wrapper = Wrapper.from_dict(File, {'path': __file__},
                                setdir=f'/path/to/moved/{Path(__file__).parent.name}',
                                streamdir='/irrelevant')
    assert wrapper.path == f'/path/to/moved/{Path(__file__).parent.name}/{Path(__file__).name}'


def test_dataset_userdata(tmpdir):
    wrapper = Wrapper.from_dict(TestStruct, {})
    with pytest.raises(AttributeError):
        assert wrapper.userdata

    wrapper = Wrapper.from_dict(Dataset, {})
    assert wrapper.userdata is None

    wrapper = Wrapper.from_dict(Dataset, {
        'files': [
            {'path': '/68b329da9893e34099c7d8ad5cb9c940/meta.json'},
        ],
    })
    assert wrapper.userdata is None

    wrapper = Wrapper.from_dict(Dataset, {
        'files': [
            {'path': '/68b329da9893e34099c7d8ad5cb9c940/meta.yaml'},
        ],
    })
    assert wrapper.userdata is None

    metajson = tmpdir / 'foo' / 'meta.json'
    metayaml = tmpdir / 'bar' / 'meta.yaml'
    metajson.parent.mkdir()
    metayaml.parent.mkdir()
    metajson.write_text('{"userdata": {"foo": 2}}')
    metayaml.write_text('userdata:\n  bar: 1')
    wrapper = Wrapper.from_dict(Dataset, {
        'files': [
            {'path': str(metayaml)},
            {'path': str(metajson)},
        ],
    })
    assert wrapper.userdata == {'foo': 2}

    wrapper = Wrapper.from_dict(Dataset, {
        'files': [
            {'path': str(metayaml)},
        ],
    })
    assert wrapper.userdata == {'bar': 1}
