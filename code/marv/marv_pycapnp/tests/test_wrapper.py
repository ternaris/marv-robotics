# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import capnp  # pylint: disable=unused-import

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

    builder.data = '\u03a8'.encode('utf-8')
    assert wrapper.data == '\u03a8'.encode('utf-8')
    assert isinstance(wrapper.data, bytes)

    builder.textList = ['\u03a8']
    assert wrapper.text_list == ['\u03a8']
    assert wrapper.text_list[:] == ['\u03a8']
    assert list(wrapper.text_list) == ['\u03a8']
    assert isinstance(wrapper.text_list[0], str)
    assert repr(wrapper.textList) == "['Ψ']"

    builder.dataList = ['\u03a8'.encode('utf-8')]
    assert wrapper.data_list == ['\u03a8'.encode('utf-8')]
    assert wrapper.data_list[:] == ['\u03a8'.encode('utf-8')]
    assert list(wrapper.data_list) == ['\u03a8'.encode('utf-8')]
    assert isinstance(wrapper.data_list[0], bytes)
    assert repr(wrapper.dataList) == "[b'\\xce\\xa8']"

    builder.textListInList = [[u'\u03a8'], [u'\u03a8']]
    builder.dataListInList = [[u'\u03a8'.encode('utf-8')], [u'\u03a8'.encode('utf-8')]]
    assert all(isinstance(x, str) for lst in wrapper.textListInList for x in lst)
    assert all(isinstance(x, bytes) for lst in wrapper.dataListInList for x in lst)

    nested = Wrapper.from_dict(
        schema=TestStruct,
        data={
            'text': '\u03a8',
            'data': '\u03a8'.encode('utf-8'),
            'textList': ['\u03a8'],
            'dataList': ['\u03a8'.encode('utf-8')],
            'textListInList': [['\u03a8'], [u'\u03a8']],
            'dataListInList': [['\u03a8'.encode('utf-8')], ['\u03a8'.encode('utf-8')]],
        },
    )
    builder.nestedList = [nested._reader]  # pylint: disable=protected-access
    assert isinstance(wrapper.nested_list[0].text, str)
    assert isinstance(wrapper.nested_list[0].data, bytes)
    assert isinstance(wrapper.nested_list[0].textList[0], str)
    assert isinstance(wrapper.nested_list[0].dataList[0], bytes)

    builder.unionData = '\u03a8'.encode('utf-8')
    assert isinstance(wrapper.union_data, bytes)

    builder.unionText = '\u03a8'
    assert isinstance(wrapper.union_text, str)

    builder.union.data = '\u03a8'.encode('utf-8')
    assert isinstance(wrapper.union.data, bytes)

    builder.union.text = '\u03a8'
    assert isinstance(wrapper.union.text, str)

    builder.group.text = '\u03a8'
    assert isinstance(wrapper.group.text, str)

    builder.group.data = '\u03a8'.encode('utf-8')
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

    dct = wrapper.to_dict()
    roundtrip = Wrapper.from_dict(TestStruct, dct)
    assert dct == roundtrip.to_dict()
