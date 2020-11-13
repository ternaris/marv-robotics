# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import logging
from pathlib import Path

import yaml

from marv_api import DatasetInfo as DSI
from marv_robotics.bag import dirscan, scan


def test_scan_nonbag():
    assert scan('/', [''], ['a', 'b']) == []


def test_scan_single_bags():
    assert scan('/', [''], ['foo.bag', 'bar.bag']) == [
        DSI(name='foo', files=['foo.bag']),
        DSI(name='bar', files=['bar.bag']),
    ]


def test_scan_rosbag_sets():
    assert scan('/', [''], [
        'set0_0000-00-00-00-00-00_0.bag',
        'set0_0000-01-00-00-00-00_1.bag',
        'set0_0000-02-00-00-00-00_2.bag',
        'set1_0000-00-00-00-00-00_0.bag',
        'set1_0000-01-00-00-00-00_1.bag',
        'set1_0000-02-00-00-00-00_2.bag',
        'set2.bag',
        'set2_0000-00-00-00-00-00_0.bag',
        'set2_0000-00-00-00-00-00_1.bag',
        'set2_0000-00-00-00-00-00_2.bag',
    ]) == [
        DSI(name='set0', files=['set0_0000-00-00-00-00-00_0.bag',
                                'set0_0000-01-00-00-00-00_1.bag',
                                'set0_0000-02-00-00-00-00_2.bag']),
        DSI(name='set1', files=['set1_0000-00-00-00-00-00_0.bag',
                                'set1_0000-01-00-00-00-00_1.bag',
                                'set1_0000-02-00-00-00-00_2.bag']),
        DSI(name='set2', files=['set2.bag']),
        DSI(name='set2', files=['set2_0000-00-00-00-00-00_0.bag',
                                'set2_0000-00-00-00-00-00_1.bag',
                                'set2_0000-00-00-00-00-00_2.bag']),
    ]


def test_scan_broken_set_edge_cases():
    assert scan('/', [''], [
        'set0_0000-00-00-00-00-00_0.bag',
        'set0_0000-00-00-00-00-00_2.bag',
        'set1_0000-00-00-00-00-00_1.bag',
        'set1_0000-00-00-00-00-00_2.bag',
        'set2.bag',
        'set2_0000-00-00-00-00-00_1.bag',
        'set2_0000-00-00-00-00-00_2.bag',
    ]) == [
        DSI(name='set0', files=['set0_0000-00-00-00-00-00_0.bag']),
        DSI(name='set0_0000-00-00-00-00-00_2', files=['set0_0000-00-00-00-00-00_2.bag']),
        DSI(name='set1_0000-00-00-00-00-00_1', files=['set1_0000-00-00-00-00-00_1.bag']),
        DSI(name='set1_0000-00-00-00-00-00_2', files=['set1_0000-00-00-00-00-00_2.bag']),
        DSI(name='set2', files=['set2.bag']),
        DSI(name='set2_0000-00-00-00-00-00_1', files=['set2_0000-00-00-00-00-00_1.bag']),
        DSI(name='set2_0000-00-00-00-00-00_2', files=['set2_0000-00-00-00-00-00_2.bag']),
    ]


def test_scan_without_timestamp():
    assert scan('/', [''], ['foo_0.bag', 'foo_1.bag', 'foo_3.bag', 'foo_4.bag']) == [
        DSI(name='foo', files=['foo_0.bag', 'foo_1.bag']),
        DSI(name='foo_3', files=['foo_3.bag']),
        DSI(name='foo_4', files=['foo_4.bag']),
    ]


def test_scan_without_prefix():
    assert scan('/', [''], [
        '0000-00-00-00-00-00.bag',
        '0000-00-00-00-00-00_0.bag',
        '0000-01-00-00-00-00_1.bag',
        '0000-02-00-00-00-00_2.bag',
        '0000-03-00-00-00-00_0.bag',
        '0000-04-00-00-00-00_1.bag',
        '0000-05-00-00-00-00_2.bag',
        '0000-06-00-00-00-00.bag',
        '0000-07-00-00-00-00.bag',
        '0000-08-00-00-00-00_0.bag',
        '0000-09-00-00-00-00_1.bag',
        '0000-10-00-00-00-00_2.bag',
    ]) == [
        DSI(name='0000-00-00-00-00-00', files=['0000-00-00-00-00-00.bag']),
        DSI(name='0000-00-00-00-00-00', files=[
            '0000-00-00-00-00-00_0.bag',
            '0000-01-00-00-00-00_1.bag',
            '0000-02-00-00-00-00_2.bag',
        ]),
        DSI(name='0000-03-00-00-00-00', files=[
            '0000-03-00-00-00-00_0.bag',
            '0000-04-00-00-00-00_1.bag',
            '0000-05-00-00-00-00_2.bag',
        ]),
        DSI(name='0000-06-00-00-00-00', files=['0000-06-00-00-00-00.bag']),
        DSI(name='0000-07-00-00-00-00', files=['0000-07-00-00-00-00.bag']),
        DSI(name='0000-08-00-00-00-00', files=[
            '0000-08-00-00-00-00_0.bag',
            '0000-09-00-00-00-00_1.bag',
            '0000-10-00-00-00-00_2.bag',
        ]),
    ]


def test_scan_mixed_edge_cases():
    assert scan('/', [''], [
        'set0_0000-00-00-00-00-00_0.bag',
        'set0_1.bag',
        'set0_1000-00-00-00-00-00_2.bag',
    ]) == [
        DSI(name='set0', files=['set0_0000-00-00-00-00-00_0.bag']),
        DSI(name='set0_1', files=['set0_1.bag']),
        DSI(name='set0_1000-00-00-00-00-00_2', files=['set0_1000-00-00-00-00-00_2.bag']),
    ]


def test_scan_missing_index():
    assert scan('/', [''], [
        'foo_0000-11-00-00-00-00.bag',
        'foo_0000-22-00-00-00-00.bag',
    ]) == [
        DSI(name='foo_0000-11-00-00-00-00', files=['foo_0000-11-00-00-00-00.bag']),
        DSI(name='foo_0000-22-00-00-00-00', files=['foo_0000-22-00-00-00-00.bag']),
    ]


def test_scan_with_rosbag2(caplog, tmpdir):
    # Scan normally traverses into subdirectories, details of bag detection handled above already
    dirnames = ['subdir']
    rv = scan('/scanroot', dirnames, ['foo.bag', 'bar.bag'])
    assert dirnames == ['subdir']
    assert len(rv) == 2

    # Create one fake rosbag2, the yaml on filesystem will be opened by scanner;
    # extradir and extrafile are not needed on filesystem as they are passed into scan function
    scanroot = Path(tmpdir)
    rb2 = (scanroot / 'rb2')
    rb2.mkdir()
    (rb2 / 'metadata.yaml').write_text(yaml.dump({
        'rosbag2_bagfile_information': {
            'relative_file_paths': [
                'foo.db3',
                'bar.db3',
            ],
            'storage_identifier': 'sqlite3',
            'topics_with_message_count': [],
            'version': 4,
        },
    }))
    (rb2 / 'foo.db3').write_text('')
    (rb2 / 'bar.db3').write_text('')

    # Extra dirs and files in rosbag2 are ignored and trigger warning
    dirnames = ['extradir']
    with caplog.at_level(logging.WARNING):
        rv = scan(str(rb2), dirnames, ['metadata.yaml', 'foo.db3', 'bar.db3', 'extrafile'])
    assert rv == [DSI('rb2', ['metadata.yaml', 'foo.db3', 'bar.db3'])]
    assert dirnames == []
    assert caplog.record_tuples == [
        (f'{scan.__module__}.{scan.__name__}', logging.WARNING,
         f"Ignoring subdirectories of dataset {rb2}: ['extradir']"),
        (f'{scan.__module__}.{scan.__name__}', logging.WARNING,
         f"Ignoring files not listed in metadata.yaml {rb2}: ['extrafile']"),
    ]

    # No reason for warnings
    caplog.clear()
    dirnames = []
    with caplog.at_level(logging.WARNING):
        rv = scan(str(rb2), dirnames, ['metadata.yaml', 'foo.db3', 'bar.db3'])
    assert rv == [DSI('rb2', ['metadata.yaml', 'foo.db3', 'bar.db3'])]
    assert caplog.record_tuples == []


def test_scan_not_a_rosbag2(caplog, tmpdir):
    # Create one rosbag2, the yaml on filesystem will be opened by scanner;
    # extradir and extrafile are not needed on filesystem as they are passed into scan function
    scanroot = Path(tmpdir)
    rb2 = (scanroot / 'rb2')
    rb2.mkdir()
    (rb2 / 'metadata.yaml').write_text(yaml.dump({
        'NOT_rosbag2': {
            'relative_file_paths': [
                'foo.db3',
                'bar.db3',
            ],
        },
    }))

    # Extra dirs and files in rosbag2 are ignored and trigger warning
    dirnames = ['extradir']
    with caplog.at_level(logging.WARNING):
        rv = scan(str(rb2), dirnames, ['metadata.yaml', 'foo.db3', 'bar.db3', 'extrafile'])
    assert len(rv) == 0
    assert dirnames == ['extradir']
    assert caplog.record_tuples == []


def test_dirscan_with_rosbag2(caplog, tmpdir):
    # subdirectories are recursed if no bag files exist in directory
    dirnames = ['subdir']
    rv = dirscan('/scanroot', dirnames, ['no_bag_file'])
    assert len(rv) == 0
    assert dirnames == ['subdir']

    # subdirectories are not recursed if one bag in directory; additional files are included
    # warning is triggered if subdirectories exist
    dirnames = ['subdir']
    with caplog.at_level(logging.WARNING):
        rv = dirscan('/scanroot/bagdir', dirnames, ['one.bag', 'other.file'])
    assert rv == [DSI('bagdir', ['one.bag', 'other.file'])]
    assert dirnames == []
    assert caplog.record_tuples == [
        (f'{dirscan.__module__}.{dirscan.__name__}', logging.WARNING,
         "Ignoring subdirectories of dataset /scanroot/bagdir: ['subdir']"),
    ]

    # Create one fake rosbag2, the yaml on filesystem will be opened by scanner;
    scanroot = Path(tmpdir)
    rb2 = (scanroot / 'rb2')
    rb2.mkdir()
    (rb2 / 'metadata.yaml').write_text(yaml.dump({
        'rosbag2_bagfile_information': {
            'relative_file_paths': [
                'foo.db3',
                'bar.db3',
            ],
            'storage_identifier': 'sqlite3',
            'topics_with_message_count': [],
            'version': 4,
        },
    }))
    (rb2 / 'foo.db3').write_text('')
    (rb2 / 'bar.db3').write_text('')
    dirnames = ['extradir']
    with caplog.at_level(logging.WARNING):
        rv = dirscan(str(rb2), dirnames, ['metadata.yaml', 'foo.db3', 'bar.db3'])
    assert rv == [DSI('rb2', ['metadata.yaml', 'foo.db3', 'bar.db3'])]
    assert dirnames == []
