# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import capnp

from marv_pycapnp import Wrapper

from .test_wrapper_capnp import TestStruct


def test():
    builder = TestStruct.new_message()
    reader = builder.as_reader()
    wrapper = Wrapper(reader, streamdir=None, setdir=None)
    assert repr(wrapper) == '<Wrapper marv_pycapnp.tests.test_wrapper_capnp:TestStruct>'

    builder.text = u'\u03a8'
    assert wrapper.text == u'\u03a8'
    assert isinstance(wrapper.text, unicode)

    builder.data = u'\u03a8'.encode('utf-8')
    assert wrapper.data == u'\u03a8'.encode('utf-8')
    assert isinstance(wrapper.data, str)

    builder.textList = [u'\u03a8']
    assert wrapper.text_list == [u'\u03a8']
    assert wrapper.text_list[:] == [u'\u03a8']
    assert list(wrapper.text_list) == [u'\u03a8']
    assert isinstance(wrapper.text_list[0], unicode)
    assert repr(wrapper.textList) == "[u'\\u03a8']"

    builder.dataList = [u'\u03a8'.encode('utf-8')]
    assert wrapper.data_list == [u'\u03a8'.encode('utf-8')]
    assert wrapper.data_list[:] == [u'\u03a8'.encode('utf-8')]
    assert list(wrapper.data_list) == [u'\u03a8'.encode('utf-8')]
    assert isinstance(wrapper.data_list[0], str)
    assert repr(wrapper.dataList) == "['\\xce\\xa8']"

    nested = Wrapper.from_dict(
        schema=TestStruct,
        data={
            'text': u'\u03a8',
            'data': u'\u03a8'.encode('utf-8'),
            'textList': [u'\u03a8'],
            'dataList': [u'\u03a8'.encode('utf-8')],
        }
    )
    builder.nestedList = [nested._reader]
    assert isinstance(wrapper.nested_list[0].text, unicode)
    assert isinstance(wrapper.nested_list[0].data, str)
    assert isinstance(wrapper.nested_list[0].textList[0], unicode)
    assert isinstance(wrapper.nested_list[0].dataList[0], str)

    builder.unionData = u'\u03a8'.encode('utf-8')
    assert isinstance(wrapper.union_data, str)

    builder.unionText = u'\u03a8'
    assert isinstance(wrapper.union_text, unicode)

    builder.union.data = u'\u03a8'.encode('utf-8')
    assert isinstance(wrapper.union.data, str)

    builder.union.text = u'\u03a8'
    assert isinstance(wrapper.union.text, unicode)

    builder.group.text = u'\u03a8'
    assert isinstance(wrapper.group.text, unicode)

    builder.group.data = u'\u03a8'.encode('utf-8')
    assert isinstance(wrapper.group.data, str)

    builder.enum = 'foo'
    assert wrapper.enum == 'foo'

    builder.enum = 'bar'
    assert wrapper.enum == 'bar'

    dct = wrapper.to_dict(which=True)
    assert dct == {
        'data': '\xce\xa8',
        'dataList': ['\xce\xa8'],
        'enum': 'bar',
        'group': {
            'data': '\xce\xa8',
            'text': u'\u03a8'
        },
        'nestedList': [
            {
                'data': '\xce\xa8',
                'dataList': ['\xce\xa8'],
                'enum': 'foo',
                'group': {
                    'data': '',
                    'text': u'',
                },
                'nestedList': [],
                'text': u'\u03a8',
                'textList': [u'\u03a8'],
                'union': {
                    'text': u'',
                    '_which': 'text',
                },
                'unionText': u'',
                '_which': 'unionText',
            }
        ],
        'text': u'\u03a8',
        'textList': [u'\u03a8'],
        'union': {
            'text': u'\u03a8',
            '_which': 'text',
        },
        'unionText': u'\u03a8',
        '_which': 'unionText',
    }

    dct = wrapper.to_dict()
    roundtrip = Wrapper.from_dict(TestStruct, dct)
    assert dct == roundtrip.to_dict()
