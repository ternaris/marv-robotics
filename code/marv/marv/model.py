# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import sqlite3
from collections import OrderedDict, namedtuple

import tortoise
from tortoise.fields import (RESTRICT, BooleanField, CharField, DatetimeField, FloatField,
                             ForeignKeyField, IntField, ManyToManyField, TextField)
from tortoise.models import Model

from . import model_fields as custom
from .utils import underscore_to_camelCase

STATUS = OrderedDict((
    ('error', 'ERROR: One or more errors occurred while processing this dataset'),
    ('missing', 'MISSING: One or more files of this dataset are missing'),
    ('outdated', 'OUTDATED: There are outdated nodes for this dataset'),
    ('pending', 'PENDING: There are pending node runs'),
))
STATUS_ERROR = 1
STATUS_MISSING = 2
STATUS_OUTDATED = 4
STATUS_PENDING = 8


tortoise.logger.setLevel(logging.WARN)


def patch_pypika_boolean_for_old_sqlite():
    from pypika.terms import ValueWrapper  # pylint: disable=import-outside-toplevel

    _original = ValueWrapper.get_value_sql

    def get_value_sql(self, **kwargs):
        value = _original(self, **kwargs)
        return {'true': 1, 'false': 0}.get(value, value)

    ValueWrapper.get_value_sql = get_value_sql


if sqlite3.sqlite_version_info < (3, 23, 0):
    patch_pypika_boolean_for_old_sqlite()


def make_status_property(bitmask, doc=None):
    def fget(obj):
        return obj.status & bitmask

    def fset(obj, value):
        status = obj.status or 0
        if value:
            obj.status = status | bitmask
        else:
            obj.status = status - (status & bitmask)

    def fdel(obj):
        fset(obj, False)

    return property(fget, fset, fdel, doc)


class Acn(Model):
    id = IntField(pk=True)


class Collection(Model):
    id = IntField(pk=True)
    name = CharField(max_length=32, unique=True)
    acn = ForeignKeyField('models.Acn', related_name='collections', on_delete=RESTRICT)


class Dataset(Model):
    id = IntField(pk=True)

    collection = ForeignKeyField('models.Collection', related_name='datasets')
    discarded = BooleanField(default=False)
    name = TextField()
    status = IntField(default=0)
    time_added = IntField()  # ms since epoch
    timestamp = IntField()  # ms since epoch

    setid = custom.SetIDField(unique=True)
    tags = ManyToManyField('models.Tag', related_name='datasets')
    acn = ForeignKeyField('models.Acn', related_name='datasets', on_delete=RESTRICT)
    dacn = ForeignKeyField('models.Acn', related_name='gdatasets', on_delete=RESTRICT)

    # Populated by backreferences: comments, files

    error = make_status_property(1)
    missing = make_status_property(2)
    outdated = make_status_property(4)
    pending = make_status_property(8)

    def __repr__(self):
        return f'<{type(self).__name__} {self.setid} {self.name}>'


class File(Model):
    id = IntField(pk=True)
    dataset = ForeignKeyField('models.Dataset', related_name='files')
    idx = IntField()  # files are counted per dataset

    missing = BooleanField(default=False)
    mtime = IntField()  # ms since epoch
    path = TextField()
    size = IntField()

    def __repr__(self):
        return f"<{type(self).__name__} '{self.path}'>"


class Metadata(Model):
    id = IntField(pk=True)
    key = CharField(max_length=32, unique=True)
    value = TextField()


class Comment(Model):
    id = IntField(pk=True)
    dataset = ForeignKeyField('models.Dataset', related_name='comments')

    author = TextField()
    time_added = IntField()  # ms since epoch
    text = TextField()


class Tag(Model):
    id = IntField(pk=True)
    value = CharField(max_length=255, unique=True)


class User(Model):
    id = IntField(pk=True)
    name = CharField(max_length=255, unique=True)
    password = TextField(null=True)
    given_name = TextField(null=True)
    family_name = TextField(null=True)
    email = TextField(null=True)
    realm = TextField()
    realmuid = TextField(null=True)
    active = BooleanField()
    time_created = DatetimeField(auto_now_add=True)
    time_updated = DatetimeField(auto_now=True)
    groups = ManyToManyField('models.Group', related_name='users')


class Group(Model):
    id = IntField(pk=True)
    name = CharField(max_length=255, unique=True)


__models__ = [
    Acn,
    Collection,
    Comment,
    Dataset,
    File,
    Group,
    Metadata,
    Tag,
    User,
]


ListingModel = namedtuple('ListingModel', 'Listing relations secondaries')
ListingDescriptor = namedtuple('ListingDescriptor', 'table key through rel_id listing_id')


def make_listing_model(name, filter_specs):
    models = []
    listing_name = f'l_{name}'
    listing_model_name = underscore_to_camelCase(listing_name)

    def generate_relation(fname):
        rel_name = f'{listing_name}_{fname}'
        rel_model_name = underscore_to_camelCase(rel_name)
        assert '_' not in rel_model_name, rel_model_name

        model = type(rel_model_name, (Model,), {
            'Meta': type('Meta', (), {'table': rel_name}),
            'id': IntField(pk=True),
            'value': CharField(max_length=255, index=True, unique=True),
            '__repr__': lambda self: f'<{type(self).__name__} {self.id} {self.value!r}>',
        })

        models.append(model)
        return ManyToManyField(f'models.{rel_model_name}', related_name='listing')

    coltype_factories = {
        # All dates and times in ms (since epoch)
        'datetime': lambda name: IntField(null=True),
        'filesize': lambda name: IntField(null=True),
        'float': lambda name: FloatField(null=True),
        'int': lambda name: IntField(null=True),
        'string': lambda name: TextField(null=True),
        'string[]': generate_relation,
        'subset': generate_relation,
        'timedelta': lambda name: IntField(null=True),
        'words': lambda name: TextField(null=True),
    }

    dct = {
        'Meta': type('Meta', (), {'table': listing_name}),
        'id': IntField(pk=True),
        'row': TextField(null=True),
        '__repr__': lambda self: f'<{type(self).__name__} {self.dataset_id}>',
    }

    dct.update((fspec.name, coltype_factories[fspec.value_type](fspec.name))
               for fspec in filter_specs.values()
               if fspec.name not in ('row', 'f_comments', 'f_status', 'f_tags')
               if not fspec.name.startswith('f_leaf_'))

    models.append(type(listing_model_name, (Model,), dct))
    return models


def make_table_descriptors(models):
    listing = models[-1]
    meta = listing._meta

    result = [ListingDescriptor(meta.table, '', '', '', '')]
    for key in meta.m2m_fields:
        field = meta.fields_map[key]
        table = field.model_class.Meta.table
        result.append(
            ListingDescriptor(table, key, field.through, field.forward_key, field.backward_key))

    return result
