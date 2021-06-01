# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=too-many-lines

import asyncio
import json
import re
import sqlite3
import sys
from collections import namedtuple
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import reduce
from itertools import groupby, product
from logging import getLogger
from pathlib import Path

import bcrypt
from pypika import JoinType, NullValue, Order
from pypika import SQLLiteQuery as Query
from pypika import Table, Tables, Tuple
from pypika import functions as fn
from pypika.terms import AggregateFunction, Criterion, EmptyCriterion, ValueWrapper
from tortoise import Tortoise as _Tortoise
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.transactions import current_transaction_map

from marv_api.setid import SetID

from . import utils
from .model import STATUS, STATUS_MISSING, STATUS_OUTDATED, Group, User
from .model import __models__ as MODELS
from .utils import findfirst

log = getLogger(__name__)


USERGROUP_REGEX = re.compile(r'[0-9a-zA-Z\-_\.@+]+$')

# Order corresponds to marv.model.STATUS OrderedDict
STATUS_ICON = ['fire', 'eye-close', 'warning-sign', 'time']
STATUS_JSON = [json.dumps({'icon': STATUS_ICON[i], 'title': x},
                          separators=(',', ':'))
               for i, x in enumerate(STATUS.values())]
# TODO: reconsider in case we get a couple of more states
STATUS_STRS = {
    bitmask: ','.join(filter(None,
                             (STATUS_JSON[i] if bitmask & 2**i else None
                              for i in range(len(STATUS_JSON)))))
    for bitmask in range(2**(len(STATUS_JSON)))
}


class NoSetidFound(Exception):
    pass


class MultipleSetidFound(Exception):
    pass


class UnknownOperator(Exception):
    pass


class FilterError(Exception):
    pass


class DBError(Exception):
    pass


class DBPermissionError(Exception):
    pass


class DBConflictError(Exception):
    pass


class DBVersionError(Exception):
    pass


class DBNotInitialized(Exception):
    pass


@asynccontextmanager
async def scoped_session(database, txn=None):
    """Transaction scope for database operations."""
    if txn:
        yield txn
    else:
        connection = await database.connection_queue.get()
        try:
            # pylint: disable=protected-access
            async with connection._in_transaction() as txn:
                async def exq(query, count=False):
                    cnt, res = await txn.execute_query(query.get_sql())
                    return cnt if count else res
                txn.exq = exq
                yield txn
        finally:
            await database.connection_queue.put(connection)


class JsonListAgg:
    def __init__(self):
        self.items = set()

    def step(self, item):
        if item is not None:
            self.items.add(item)

    def finalize(self):
        return json.dumps(sorted(self.items))


async def create_or_ignore(tablename, txn, **kw):
    table = Table(tablename)
    query = Query.from_(table).select(table.star)
    for col, value in kw.items():
        query = query.where(getattr(table, col) == value)
    rows = await txn.exq(query)
    if not rows:
        await txn.exq(Query.into(table).columns(*kw.keys()).insert(*kw.values()))


def run_in_transaction(func):
    async def wrapper(database, *args, txn=None, **kwargs):
        async with scoped_session(database, txn=txn) as txn:
            return await func(database, *args, txn=txn, **kwargs)

    return wrapper


class FromExceptQuery:
    class Builder:
        def __init__(self, from_=None, except_=None):
            self._from = from_
            self._except = except_

        def from_(self, term):
            self._from = term
            return self

        def except_(self, term):
            self._except = term
            return self

        def get_sql(self, **kw):
            kw['subquery'] = False
            return f'({self._from.get_sql(**kw)} EXCEPT {self._except.get_sql(**kw)})'

    @classmethod
    def from_(cls, term):
        return cls.Builder(from_=term)

    @classmethod
    def except_(cls, term):
        return cls.Builder(except_=term)


class ValuesTuple(Tuple):
    def get_sql(self, **kw):
        sql = f'(VALUES {",".join(x.get_sql(**kw) for x in self.values)})'
        if self.alias:
            return f'{sql} AS {self.alias}'
        return sql


class GroupConcat(AggregateFunction):
    def __init__(self, term, alias=None):
        super().__init__('GROUP_CONCAT', term, alias=alias)


class JsonGroupArray(AggregateFunction):
    def __init__(self, term, alias=None):
        super().__init__('JSON_GROUP_ARRAY', term, alias=alias)


class EscapableLikeCriterion(Criterion):
    operator = 'LIKE'

    def __init__(self, left, right, escchr, alias=None):
        super().__init__(alias)
        self.left = left
        self.right = right
        self.escchr = escchr

    def fields(self):
        return self.left.fields() + self.right.fields()

    def get_sql(self, with_alias=False, **kwargs):  # pylint: disable=arguments-differ
        sql = (f'{self.left.get_sql(**kwargs)} {self.operator} {self.right.get_sql(**kwargs)} '
               f'ESCAPE "{self.escchr}"')
        if with_alias and self.alias:
            return f'{sql} "{self.alias}"'
        return sql


class EscapableNotlikeCriterion(EscapableLikeCriterion):
    operator = 'NOT LIKE'


def esc(value, escchr='$'):
    return value.replace(f'{escchr}', f'{escchr}{escchr}')\
                .replace('_', f'{escchr}_')\
                .replace('%', f'{escchr}%')


def escaped_contains(field, value, escchr='$'):
    return EscapableLikeCriterion(field, ValueWrapper(f'%{esc(value, escchr)}%'), escchr)


def escaped_startswith(field, value, escchr='$'):
    return EscapableLikeCriterion(field, ValueWrapper(f'{esc(value, escchr)}%'), escchr)


def escaped_endswith(field, value, escchr='$'):
    return EscapableLikeCriterion(field, ValueWrapper(f'%{esc(value, escchr)}'), escchr)


def escaped_not_startswith(field, value, escchr='$'):
    return EscapableNotlikeCriterion(field, ValueWrapper(f'{esc(value, escchr)}%'), escchr)


OPS = {
    'between': lambda f, v: f.between(*v),
    'endswith': escaped_endswith,
    'eq': lambda f, v: f.eq(v),
    'gt': lambda f, v: f.gt(v),
    'gte': lambda f, v: f.gte(v),
    'ilike': lambda f, v: f.ilike(v),
    'in': lambda f, v: f.isin(v),
    'is': lambda f, v: f.isnull() if v is None else f.eq(v),
    'isnot': lambda f, v: f.notnull() if v is None else f.ne(v),
    'like': lambda f, v: f.like(v),
    'lt': lambda f, v: f.lt(v),
    'lte': lambda f, v: f.lte(v),
    'ne': lambda f, v: f.ne(v),
    'notbetween': lambda f, v: f.between(*v).negate(),
    'notilike': lambda f, v: f.not_ilike(v),
    'notin': lambda f, v: f.notin(v),
    'notlike': lambda f, v: f.not_like(v),
    'startswith': escaped_startswith,
    'substring': escaped_contains,
}


def resolve_filter(table, fltr, models):  # noqa: C901  pylint: disable=too-many-branches
    if not isinstance(fltr, dict):
        raise FilterError(f'Expected dict not {fltr!r}')

    operator = fltr.get('op')
    if not operator:
        raise FilterError(f"Missing 'op' in {fltr!r}")
    if not isinstance(operator, str):
        raise FilterError(f'Expected string not {operator!r}')

    value = fltr.get('value')
    name = fltr.get('name')

    if operator == 'and':
        return reduce(lambda x, y: x & resolve_filter(table, y, models), value, EmptyCriterion())
    if operator == 'or':
        return reduce(lambda x, y: x | resolve_filter(table, y, models), value, EmptyCriterion())
    if operator == 'not':
        return resolve_filter(table, value, models).negate()

    if not isinstance(name, str):
        raise FilterError(f"Missing 'name' in {fltr!r}")

    if name.startswith('dataset.') and table._table_name.startswith('l_'):
        name = name[8:]
        tablemeta = findfirst(lambda x: x._meta.table == 'dataset', models)._meta
    else:
        tablemeta = findfirst(lambda x: x._meta.table == table._table_name, models)._meta

    if '.' in name:
        fieldname, subname = name.split('.', 1)
        if fieldname in tablemeta.backward_fk_fields:
            field = tablemeta.fields_map[fieldname]
            subtable = Table(field.model_class._meta.table)
            resolved = resolve_filter(subtable, {'op': operator, 'name': subname, 'value': value},
                                      models)
            return getattr(table, 'id').isin(Query.from_(subtable)
                                             .select(getattr(subtable, field.relation_field))
                                             .where(resolved))

        if fieldname in tablemeta.m2m_fields:
            field = tablemeta.fields_map[fieldname]
            through = Table(field.through)
            rel = Table(field.model_class._meta.table)
            resolved = resolve_filter(rel, {'op': operator, 'name': subname, 'value': value},
                                      models)
            return getattr(table, 'id').isin(Query.from_(through)
                                             .join(rel)
                                             .on(getattr(through, field.forward_key) == rel.id)
                                             .where(resolved)
                                             .select(getattr(through, field.backward_key))
                                             .distinct())

        raise FilterError(f'Field {fieldname!r} not on model {tablemeta.table!r}')

    if name not in tablemeta.db_fields:
        raise FilterError(f'Field {name!r} not on model {tablemeta.table!r}')

    if operator not in OPS:
        raise FilterError(f'Unknown operator {operator!r}')

    field = getattr(table, name)
    return OPS[operator](field, value)


def cleanup_attrs(items):
    return [
        {k: x[k] for k in x.keys() if k not in ['acn_id', 'dacn_id', 'password', 'row']}
        for x in items
    ]


def cast_fields(keys, values):
    tmap = {
        'setid': SetID,
    }
    return [tmap.get(k, lambda x: x)(v) for k, v in zip(keys, values)]


def modelize(items, relations):
    res = []
    if not items:
        return res

    keys = items[0].keys()
    relidx = [i for i, x in enumerate(keys) if x == 'id'] + [len(keys)]

    dataset = namedtuple('dataset', keys[:relidx[1]] + list(relations))
    types = [
        namedtuple(x, keys[relidx[i+1]:relidx[i+2]])
        for i, x in enumerate(relations)
    ]

    for _, group in groupby(items, lambda x: x[0]):
        group = list(group)
        related = [
            sorted(set(filter(lambda x: x.id, (
                x(*y[relidx[i+1]:relidx[i+2]]) for y in group
            ))), key=lambda x: x.id)
            for i, x in enumerate(types)
        ]
        res.append(dataset(*(cast_fields(keys[:relidx[1]], group[0]) + related)))
    return res


def dt_to_sec(dtime):
    """Return seconds since epoch for datetime object."""
    return int(datetime.fromisoformat(dtime).replace(tzinfo=timezone.utc).timestamp())


async def get_items_for_query(query, txn):
    return [
        {k: x[k] for k in x.keys()}
        for x in (await txn.execute_query(query.get_sql()))[1]
    ]


async def process_items(query, delkeys, getkey, txn):
    items = await get_items_for_query(query, txn)
    res = {}
    for did, grp in groupby(items, key=lambda x: x['dataset_id']):
        assert did not in res
        res[did] = lst = []
        for item in grp:
            del item['id']
            del item['dataset_id']
            for delkey in delkeys:
                del item[delkey]
            lst.append(item[getkey] if getkey else item)
    return res


async def dump_users_groups(tables, dump, txn):
    group_t = tables.pop('group')
    user_t = tables.pop('user')
    user_group_t = tables.pop('user_group')
    groups = {}
    items = await get_items_for_query(Query.from_(user_group_t)
                                      .join(group_t)
                                      .on(user_group_t.group_id == group_t.id)
                                      .select('*')
                                      .where(~escaped_startswith(group_t.name, 'marv:'))
                                      .orderby(user_group_t.user_id)
                                      .orderby(group_t.name),
                                      txn)
    for uid, grp in groupby(items, key=lambda x: x['user_id']):
        assert uid not in groups
        groups[uid] = lst = []
        for group in grp:
            del group['id']
            del group['group_id']
            del group['user_id']
            name = group.pop('name')
            assert not group
            lst.append(name)

    dump['users'] = users = []
    items = await get_items_for_query(Query.from_(user_t)
                                      .select('*')
                                      .where(user_t.name != 'marv:anonymous')
                                      .orderby(user_t.name),
                                      txn)
    for user in items:
        uid = user.pop('id')
        user['groups'] = groups.pop(uid, [])
        user['time_created'] = dt_to_sec(user['time_created'])
        user['time_updated'] = dt_to_sec(user['time_updated'])
        users.append(user)
    assert not groups, groups


async def dump_acns(tables, dump, txn):  # pylint: disable=unused-argument
    del tables['acn']


async def dump_comments(tables, dump, txn):
    table = tables.pop('comment')
    dump['comments'] = await process_items(Query.from_(table)
                                           .select(table.star)
                                           .orderby(table.dataset_id)
                                           .orderby(table.id),
                                           (),
                                           None,
                                           txn)


async def dump_files(tables, dump, txn):
    table = tables.pop('file')
    dump['files'] = await process_items(Query.from_(table)
                                        .select(table.star)
                                        .orderby(table.dataset_id)
                                        .orderby(table.id),
                                        ('idx',),
                                        None,
                                        txn)


async def dump_tags(tables, dump, txn):
    dataset_tag_t = tables.pop('dataset_tag')
    tag_t = tables.pop('tag')
    dump['tags'] = await process_items(Query.from_(dataset_tag_t)
                                       .join(tag_t)
                                       .on(dataset_tag_t.tag_id == tag_t.id)
                                       .select('*')
                                       .orderby(dataset_tag_t.dataset_id)
                                       .orderby(tag_t.value),
                                       ('tag_id',),
                                       'value',
                                       txn)


async def dump_datasets(tables, dump, txn):
    comments = dump.pop('comments')
    files = dump.pop('files')
    tags = dump.pop('tags')

    dump['datasets'] = collections = {}
    collection_t = tables.pop('collection')
    dataset_t = tables.pop('dataset')
    items = await get_items_for_query(Query.from_(dataset_t)
                                      .join(collection_t)
                                      .on(dataset_t.collection_id == collection_t.id)
                                      .select(dataset_t.star, collection_t.name.as_('collection'))
                                      .orderby(dataset_t.setid),
                                      txn)
    for dataset in items:
        did = dataset.pop('id')
        del dataset['acn_id']
        del dataset['collection_id']
        del dataset['dacn_id']
        dataset['comments'] = comments.pop(did, [])
        dataset['files'] = files.pop(did)
        dataset['tags'] = tags.pop(did, [])
        collections.setdefault(dataset.pop('collection'), []).append(dataset)

    assert not comments, comments
    assert not files, files
    assert not tags, tags


async def dump_metadata(tables, dump, txn):  # pylint: disable=unused-argument
    tables.pop('metadata')


async def restore_users(site, dct, txn):
    users = dct.pop('users')
    for user in users or []:
        user.setdefault('realm', 'marv')
        user.setdefault('realmuid', '')
        groups = user.pop('groups', [])
        await site.db.user_add(_restore=True, txn=txn, **user)
        for grp in groups:
            try:
                await site.db.group_adduser(grp, user['name'], txn=txn)
            except ValueError:
                await site.db.group_add(grp, txn=txn)
                await site.db.group_adduser(grp, user['name'], txn=txn)


async def restore_datasets(site, dct, txn):
    datasets = dct.pop('datasets')
    for key, sets in datasets.items():
        await site.collections[key].restore_datasets(sets, txn)


class Tortoise(_Tortoise):
    @classmethod
    def _discover_models(cls, model, app_label):  # pylint: disable=arguments-differ
        model._meta.app = app_label
        model._meta.finalise_pk()
        return [model]


ACLS = {
    'comment': ['__authenticated__'],
    'delete': ['admin'],
    'download_raw': ['__authenticated__'],
    'list': ['__authenticated__'],
    'read': ['__authenticated__'],
    'tag': ['__authenticated__'],
}


class Database:
    # pylint: disable=too-many-public-methods

    VERSION = '21.05'
    DUMP_VERSION = '21.05'

    EXPORT_HANDLERS = (
        ({'group', 'user', 'user_group'}, dump_users_groups),
        ({'acn'}, dump_acns),
        ({'comment'}, dump_comments),
        ({'file'}, dump_files),
        ({'tag', 'dataset_tag'}, dump_tags),
        ({'dataset', 'collection'}, dump_datasets),
        ({'metadata'}, dump_metadata),
    )

    IMPORT_HANDLERS = (
        ({'users'}, restore_users),
        ({'datasets'}, restore_datasets),
    )

    MODELS = MODELS

    def __init__(self, listing_models, config):
        self.connections = []
        self.connection_queue = asyncio.Queue()
        self.listing_models = listing_models
        self.config = config
        self.acls = ACLS.copy()
        if self.config.marv.ce_anonymous_readonly_access:
            self.acls.update({
                'download_raw': ['__unauthenticated__', '__authenticated__'],
                'list': ['__unauthenticated__', '__authenticated__'],
                'read': ['__unauthenticated__', '__authenticated__'],
            })

    async def initialize_connections(self):
        defcon = Tortoise.get_connection('default')
        for idx in range(48):
            name = f'connection_{idx}'
            db_params = defcon.pragmas.copy()
            db_params['connection_name'] = name
            connection = defcon.__class__(defcon.filename, **db_params)
            await connection.create_connection(with_db=True)

            await connection._connection._execute(  # pylint: disable=protected-access
                connection._connection._conn.create_aggregate,  # pylint: disable=protected-access
                'JSON_GROUP_ARRAY', 1, JsonListAgg,
            )

            current_transaction_map[name] = ContextVar(name, default=connection)
            await self.connection_queue.put(connection)
            self.connections.append(connection)

    async def close_connections(self):
        for connection in self.connections:
            # pylint: disable=protected-access
            cursor = await connection._connection.execute('PRAGMA optimize')
            await cursor.close()
            await connection.close()
            current_transaction_map.pop(connection.connection_name)
        self.connections.clear()

    @run_in_transaction
    async def authenticate(self, username, password, txn=None):
        if not username or not password:
            return False
        try:
            user = await User.get(name=username, active=True, realm='marv').using_db(txn)
        except DoesNotExist:
            return False
        return bcrypt.checkpw(password.encode(), user.password.encode())

    @run_in_transaction
    async def bulk_um(self, users_add, users_remove, groups_add, groups_remove,  # noqa: C901
                      groups_add_users, groups_remove_users, txn=None):
        # pylint: disable=too-many-arguments
        try:
            everybody = await Group.get(name='marv:users').using_db(txn)

            for name in users_remove:
                user = await User.get(name=name).using_db(txn)
                group = await Group.get(name=f'marv:user:{name}').using_db(txn)
                await user.groups.remove(group, everybody, using_db=txn)
                await user.delete(using_db=txn)
                await group.delete(using_db=txn)

            for name in users_add:
                if not USERGROUP_REGEX.match(name):
                    raise DBError('User name can only contain alphanumeric characters and [-_+@.]')
                user = await User.create(name=name, realm='marv', active=True, using_db=txn)
                await user.groups.add(
                    await Group.create(name=f'marv:user:{name}', using_db=txn),
                    everybody,
                    using_db=txn,
                )

            for name in groups_remove:
                await Group.get(name=name).using_db(txn).delete()

            for name in groups_add:
                if not USERGROUP_REGEX.match(name):
                    raise DBError(
                        'Group name can only contain alphanumeric characters and [-_+@.]',
                    )
                await Group.create(name=name, using_db=txn)

            for name, users in groups_remove_users:
                group = await Group.get(name=name).using_db(txn)
                users = await User.filter(name__in=users).using_db(txn)
                await group.users.remove(*users, using_db=txn)

            for name, users in groups_add_users:
                group = await Group.get(name=name).using_db(txn)
                users = await User.filter(name__in=users).using_db(txn)
                await group.users.add(*users, using_db=txn)
        except DoesNotExist:
            raise DBError('Entity does not exist')
        except IntegrityError:
            raise DBError('Entity exists already')

    @run_in_transaction
    async def user_add(self, name, password, realm, realmuid, given_name=None, family_name=None,
                       email=None, active=True, time_created=None, time_updated=None, _restore=None,
                       txn=None):
        # pylint: disable=too-many-arguments
        if not USERGROUP_REGEX.match(name) and not _restore:
            raise DBError('User name can only contain alphanumeric characters and [-_+@.]')
        if not _restore and password is not None:
            password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        now = datetime.utcnow()  # noqa: DTZ
        time_created = datetime.utcfromtimestamp(time_created) if time_created else now
        time_updated = datetime.utcfromtimestamp(time_updated) if time_updated else now
        try:
            user = await User.create(name=name, password=password, realm=realm,
                                     given_name=given_name, family_name=family_name,
                                     email=email, realmuid=realmuid, active=active,
                                     time_created=time_created, time_updated=time_updated,
                                     using_db=txn)
            if name != 'marv:anonymous':
                everybody = await Group.get(name='marv:users').using_db(txn)
                await user.groups.add(
                    await Group.create(name=f'marv:user:{name}', using_db=txn),
                    everybody,
                    using_db=txn,
                )
            if _restore:
                user = Table('user')
                await txn.exq(Query.update(user)
                              .set(user.time_updated, time_updated)
                              .where(user.name == name))
        except IntegrityError:
            raise ValueError(f'User {name} exists already')
        return user

    @run_in_transaction
    async def user_rm(self, username, txn=None):
        try:
            user = await User.get(name=username).using_db(txn)
            group = await Group.get(name=f'marv:user:{username}').using_db(txn)
            everybody = await Group.get(name='marv:users').using_db(txn)
            await user.groups.remove(group, everybody, using_db=txn)
            await user.delete(using_db=txn)
            await group.delete(using_db=txn)

            await user.delete(using_db=txn)
        except DoesNotExist:
            raise ValueError(f'User {username} does not exist')

    @run_in_transaction
    async def user_pw(self, username, password, txn=None):
        try:
            user = await User.get(name=username).using_db(txn)
        except DoesNotExist:
            raise ValueError(f'User {username} does not exist')

        user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user.time_updated = int(utils.now())
        await user.save(using_db=txn)

    @run_in_transaction
    async def group_add(self, groupname, txn=None):
        if not USERGROUP_REGEX.match(groupname):
            raise DBError('Group name can only contain alphanumeric characters and [-_+@.]')
        try:
            await Group.create(name=groupname, using_db=txn)
        except IntegrityError:
            raise ValueError(f'Group {groupname} exists already')

    @run_in_transaction
    async def group_rm(self, groupname, txn=None):
        try:
            group = await Group.get(name=groupname).using_db(txn)
            await group.delete(using_db=txn)
        except DoesNotExist:
            raise ValueError(f'Group {groupname} does not exist')

    @run_in_transaction
    async def group_adduser(self, groupname, username, txn=None):
        try:
            group = await Group.get(name=groupname).using_db(txn)
        except DoesNotExist:
            raise ValueError(f'Group {groupname} does not exist')
        try:
            user = await User.get(name=username).using_db(txn)
        except DoesNotExist:
            raise ValueError(f'User {username} does not exist')
        await group.users.add(user, using_db=txn)

    @run_in_transaction
    async def group_rmuser(self, groupname, username, txn=None):
        try:
            group = await Group.get(name=groupname).using_db(txn)
        except DoesNotExist:
            raise ValueError(f'Group {groupname} does not exist')
        try:
            user = await User.get(name=username).using_db(txn)
        except DoesNotExist:
            raise ValueError(f'User {username} does not exist')
        await group.users.remove(user, using_db=txn)

    @run_in_transaction
    async def get_users(self, deep=False, txn=None):
        query = User.all().using_db(txn).order_by('name')
        if deep:
            query = query.prefetch_related('groups')
        return await query

    @run_in_transaction
    async def get_user_by_name(self, name, deep=False, txn=None):
        query = User.filter(name=name).using_db(txn)
        if deep:
            query = query.prefetch_related('groups')
        return await query.first()

    @run_in_transaction
    async def get_user_by_realmuid(self, realm, realmuid, deep=False, txn=None):
        query = User.filter(realm=realm, realmuid=realmuid).using_db(txn)
        if deep:
            query = query.prefetch_related('groups')
        return await query.first()

    @run_in_transaction
    async def get_groups(self, deep=False, txn=None):
        query = Group.all().using_db(txn).order_by('name')
        if deep:
            query = query.prefetch_related('users')
        return await query

    @run_in_transaction
    async def get_acl(self, model, id, user, default, txn=None):
        # pylint: disable=unused-argument, too-many-arguments
        return default

    @staticmethod
    def if_admin(username, query):
        user, user_group, group = Tables('user', 'user_group', 'group')
        return (query
                .join(user)
                .cross()
                .join(user_group)
                .on(user.id == user_group.user_id)
                .join(group)
                .on(user_group.group_id == group.id)
                .where((group.name == 'admin') & (user.name == username)))

    def generate_crit(self, ids, empty, user, action):
        if user == '::':
            return ids
        groups = self.acls[action]
        if user == 'marv:anonymous':
            if '__unauthenticated__' in groups:
                return ids
            return empty

        if '__authenticated__' in groups:
            return ids

        return self.if_admin(user, ids)

    def get_actionable(self, modelname, user, action):
        model = Table(modelname)
        query = Query.from_(model).select(model.id)
        return self.generate_crit(query, query.where(model.id.isnull()), user, action)

    def get_resolve_value_query(self, rel, relations, user, action):
        # pylint: disable=unused-argument
        out, tmp = Tables('out', 'tmp')
        query = Query.with_(Query.with_(Query.from_(ValuesTuple(*relations))
                                        .select('*'), 'tmp(value, back_id)')
                            .from_(tmp)
                            .join(rel)
                            .on(tmp.value == rel.value)
                            .select(rel.id, tmp.back_id), 'out(rel_id, back_id)')\
                     .from_(out)\
                     .select(out.rel_id, out.back_id)

        ids = Table('ids')
        empty = Query.select(ids.star).from_(ValuesTuple(Tuple(0, 0)).as_(ids)).where(NullValue())

        return self.generate_crit(query, empty, user, action)

    def id_crit(self, ids, user, action):
        dataset = Table('dataset')
        tids = Table('tids')
        ids = Query.from_(ValuesTuple(*[(x,) for x in ids]).as_('tids')).select(tids.star)
        return dataset.id.isin(self.generate_crit(ids, Tuple(), user, action))

    def setid_crit(self, ids, user, action):
        dataset = Table('dataset')
        tids = Table('tids')
        ids = Query.from_(ValuesTuple(*[(str(x),) for x in ids]).as_('tids')).select(tids.star)
        return dataset.setid.isin(self.generate_crit(ids, Tuple(), user, action))

    @run_in_transaction
    async def resolve_shortids(self, prefixes, discarded=False, txn=None):
        setids = set()
        dataset = Table('dataset')
        for prefix in prefixes:
            if isinstance(prefix, SetID):
                prefix = str(prefix)

            setid = await txn.exq(Query.from_(dataset)
                                  .select('setid')
                                  .where(escaped_startswith(dataset.setid, prefix)
                                         & (dataset.discarded == discarded))
                                  .limit(2))

            if not setid:
                discarded = 'discarded ' if discarded else ''
                raise NoSetidFound(f'{prefix} does not match any {discarded}dataset')
            if len(setid) > 1:
                matches = '\n  '.join([f'{x}' for x in setid])
                raise MultipleSetidFound(f'{prefix} matches multiple:\n'
                                         f'  {matches}\n')
            setids.add(SetID(setid[0][0]))
        return sorted(setids)

    @run_in_transaction
    async def get_collections(self, user, txn=None):  # pylint: disable=unused-argument
        collection = Table('collection')
        return [
            {'id': x, 'name': y}
            for x, y in await txn.exq(Query.from_(collection)
                                      .select(collection.id, collection.name)
                                      .where(collection.id.isin(
                                          self.get_actionable('collection', user, 'list')))
                                      .orderby(collection.name))
        ]

    async def _get_datasets_by_crit(self, crit, prefetch, txn):
        dataset = Table('dataset')
        query = Query.from_(dataset).where(crit).select(dataset.star)
        for related in prefetch:
            table = Table(related[:-1])
            if related == 'collections':
                query = query.join(table)\
                             .on(dataset.collection_id == table.id)\
                             .select(table.star)
            elif related == 'tags':
                through = Table('dataset_tag')
                query = query.join(through, how=JoinType.left_outer)\
                             .on(dataset.id == through.dataset_id)\
                             .join(table, how=JoinType.left_outer)\
                             .on(through.tag_id == table.id)\
                             .select(table.star)
            else:
                query = query.join(table, how=JoinType.left_outer)\
                             .on(table.dataset_id == dataset.id)\
                             .select(table.star)
        items = await txn.exq(query)
        return modelize(items, prefetch)

    @run_in_transaction
    async def get_datasets_by_setids(self, setids, prefetch, user, action=None, txn=None):
        # pylint: disable=too-many-arguments
        ret = await self._get_datasets_by_crit(self.setid_crit(setids, user, action), prefetch, txn)
        if len(ret) != len(setids):
            raise DBPermissionError
        return ret

    @run_in_transaction
    async def get_datasets_by_dbids(self, ids, prefetch, user, action=None, txn=None):
        # pylint: disable=too-many-arguments
        ret = await self._get_datasets_by_crit(self.id_crit(ids, user, action), prefetch, txn)
        if len(ret) != len(ids):
            raise DBPermissionError
        return ret

    @run_in_transaction
    async def get_filepath_by_setid_idx(self, setid, idx, user, txn=None):
        dataset, file = Tables('dataset', 'file')
        res = await txn.exq(Query.from_(file)
                            .join(dataset)
                            .on(file.dataset_id == dataset.id)
                            .where((file.idx == idx)
                                   & self.setid_crit([setid], user, 'download_raw'))
                            .select('path'))
        if not res:
            raise DBPermissionError
        return res[0]['path']

    @run_in_transaction
    async def get_datasets_for_collections(self, collections, txn=None):
        dataset = Table('dataset')
        bitmask = ValueWrapper(STATUS_MISSING)
        query = Query.from_(dataset)\
                     .select('setid')\
                     .where((dataset.discarded.eq(False))
                            & dataset.status.bitwiseand(bitmask).ne(bitmask))
        if collections is not None:
            collection = Table('collection')
            query = query.join(collection)\
                         .on(dataset.collection_id == collection.id)\
                         .where(collection.name.isin(collections))
        return [SetID(x['setid']) for x in await txn.exq(query)]

    async def _set_dataset_discarded_by_crit(self, crit, state, txn):
        dataset = Table('dataset')
        return await txn.exq(Query.update(dataset)
                             .set(dataset.discarded, state)
                             .where(crit), count=True)

    @run_in_transaction
    async def discard_datasets_by_setids(self, setids, state=True, txn=None):
        await self._set_dataset_discarded_by_crit(self.setid_crit(setids, '::', None), state, txn)

    @run_in_transaction
    async def discard_datasets_by_dbids(self, ids, state, user, txn=None):
        count = await self._set_dataset_discarded_by_crit(self.id_crit(ids, user, 'delete'),
                                                          state, txn)
        if count != len(ids):
            raise DBPermissionError

    @run_in_transaction
    async def cleanup_discarded(self, descs, txn=None):
        collection, dataset = Tables('collection', 'dataset')
        datasets = await txn.exq(Query.from_(dataset)
                                 .join(collection)
                                 .on(dataset.collection_id == collection.id)
                                 .select(collection.name, dataset.id)
                                 .where(dataset.discarded.eq(True))
                                 .orderby(collection.name))
        if not datasets:
            return

        datasets = [
            (col, [x[1] for x in tuples])
            for col, tuples in groupby(datasets, lambda x: x[0])
        ]
        for col, ids in datasets:
            await txn.exq(Query.from_(dataset)
                          .where(dataset.id.isin(ids))
                          .delete())

            for table in (Table('dataset_tag'), Table('comment'), Table('file')):
                await txn.exq(Query.from_(table)
                              .where(table.dataset_id.isin(ids))
                              .delete())

            tbls = descs[col]
            assert not tbls[0].through, 'Listing table should be first'
            listing = Table(tbls[0].table)

            await txn.exq(Query.from_(listing)
                          .where(listing.id.isin(ids))
                          .delete())

            for desc in [x for x in tbls if x.through]:
                through = Table(desc.through)
                id_field = getattr(through, desc.listing_id)
                await txn.exq(Query.from_(through)
                              .where(id_field.isin(ids))
                              .delete())

    @run_in_transaction
    async def bulk_comment(self, comments, user, txn=None):
        comment, dataset, tmp, user_t = Tables('comment', 'dataset', 'tmp', 'user')
        comments = [(x['dataset_id'], x['author'], x['time_added'], x['text']) for x in comments]
        query = Query.into(comment)\
                     .columns('dataset_id', 'author', 'time_added', 'text')\
                     .from_(Query.with_(Query.from_(ValuesTuple(*comments))
                                        .select('*'), 'tmp(dataset_id, author, time_added, text)')
                            .from_(tmp)
                            .join(dataset)
                            .on(tmp.dataset_id == dataset.id)
                            .where(self.id_crit([x[0] for x in comments], user, 'comment'))
                            .join(user_t)
                            .on(tmp.author == user_t.name)
                            .select(tmp.star))\
                     .select('*')
        count = await txn.exq(query, count=True)
        if count != len(comments):
            raise DBPermissionError

    @run_in_transaction
    async def comment_by_setids(self, setids, author, text, txn=None):
        comment, dataset, tmp, user = Tables('comment', 'dataset', 'tmp', 'user')
        time_added = int(utils.now() * 1000)
        query = Query.into(comment)\
                     .columns('dataset_id', 'author', 'time_added', 'text')\
                     .from_(Query.with_(Query.from_(ValuesTuple((author, time_added, text)))
                                        .select('*'), 'tmp(author, time_added, text)')
                            .from_(dataset)
                            .join(tmp)
                            .cross()
                            .join(user)
                            .on(tmp.author == user.name)
                            .where(dataset.setid.isin([str(x) for x in setids]))
                            .select(dataset.id, tmp.star))\
                     .select('*')
        count = await txn.exq(query, count=True)
        if count != len(setids):
            raise DBError(f'Commenting failed. User {author!r} or one of the datasets are missing')

    @run_in_transaction
    async def delete_comments_by_ids(self, ids, txn=None):
        comment = Table('comment')
        await txn.exq(Query.from_(comment)
                      .where(comment.id.isin(ids))
                      .delete())

    @run_in_transaction
    async def get_comments_by_setids(self, setids, txn=None):
        comment, dataset = Tables('comment', 'dataset')
        if setids:
            crit = dataset.setid.isin([str(x) for x in setids])
        else:
            crit = dataset.discarded.ne(True)
        query = Query.from_(comment)\
                     .join(dataset).on(comment.dataset_id == dataset.id)\
                     .select(comment.star, dataset.star)\
                     .where(crit)
        items = await txn.exq(query)
        return modelize(items, ['dataset'])

    async def _ensure_values(self, tablename, values, user, txn):
        # pylint: disable=unused-argument
        table = Table(tablename)
        query = Query.into(table)\
                     .columns('value')\
                     .from_(FromExceptQuery
                            .from_(Query.from_(ValuesTuple(*values)).select('*'))
                            .except_(Query().from_(table).select(table.value)))\
                     .select('*')
        return await txn.exq(query, count=True)

    async def _ensure_refs(self, relname, throughname, rel_id, back_id, relations, user,
                           action, txn):
        # pylint: disable=too-many-arguments
        rel, through = Tables(relname, throughname)
        relid = getattr(through, rel_id)
        backid = getattr(through, back_id)
        query = Query.into(through)\
                     .columns(rel_id, back_id)\
                     .from_(FromExceptQuery
                            .from_(self.get_resolve_value_query(rel, relations, user, action))
                            .except_(Query.from_(through).select(relid, backid)))\
                     .select('*')
        return await txn.exq(query, count=True)

    async def _delete_values_without_ref(self, relname, throughname, rel_id, txn):
        rel, through = Tables(relname, throughname)
        await txn.exq(Query.from_(rel)
                      .where(rel.id.notin(Query.from_(throughname)
                                          .select(getattr(through, rel_id))
                                          .distinct()))
                      .delete())

    @run_in_transaction
    async def bulk_tag(self, add, remove, user, txn=None):
        if add:
            await self._ensure_values('tag', [(x[0],) for x in add], user, txn)
            count = await self._ensure_refs('tag', 'dataset_tag', 'tag_id', 'dataset_id', add,
                                            user, 'tag', txn)
            if count != len(add):
                raise DBPermissionError

        if remove:
            through, tag = Tables('dataset_tag', 'tag')
            query = Query.from_(through)\
                         .delete()\
                         .select(through.tag_id, through.dataset_id)\
                         .where(Tuple(through.tag_id, through.dataset_id)
                                .isin(self.get_resolve_value_query(tag, remove, user, 'tag')))
            count = await txn.exq(query, count=True)
            if count != len(remove):
                raise DBPermissionError

    @run_in_transaction
    async def update_tags_by_setids(self, setids, add, remove, idempotent=False, txn=None):
        setids = [str(x) for x in setids]
        dataset, dataset_tag, tag = Tables('dataset', 'dataset_tag', 'tag')
        tagmap = await txn.exq(Query.from_(dataset)
                               .join(dataset_tag, how=JoinType.left_outer)
                               .on(dataset.id == dataset_tag.dataset_id)
                               .join(tag, how=JoinType.left_outer)
                               .on(tag.id == dataset_tag.tag_id)
                               .select(tag.value, dataset.id)
                               .where(dataset.setid.isin(setids)))
        current = {tuple(x) for x in tagmap}
        ids = [x[1] for x in current]
        add = set(product(add, ids))
        remove = set(product(remove, ids))
        if idempotent:
            add -= current
            remove &= current
        await self.bulk_tag(add, remove, user='::', txn=txn)

    @run_in_transaction
    async def list_tags(self, collections=None, txn=None):
        collection, dataset, dataset_tag, tag = Tables('collection', 'dataset', 'dataset_tag',
                                                       'tag')
        query = Query.from_(tag)\
                     .select('value')\
                     .distinct()\
                     .orderby('value')

        if collections:
            query = query.join(dataset_tag, how=JoinType.left_outer)\
                         .on(tag.id == dataset_tag.tag_id)\
                         .join(dataset)\
                         .on(dataset_tag.dataset_id == dataset.id)\
                         .join(collection)\
                         .on(dataset.collection_id == collection.id)\
                         .where(collection.name.isin(collections))

        return [x['value'] for x in await txn.exq(query)]

    @run_in_transaction
    async def delete_comments_tags(self, setids, comments, tags, txn=None):
        dataset, dataset_tag, comment = Tables('dataset', 'dataset_tag', 'comment')
        subq = Query.from_(dataset)\
                    .select(dataset.id)\
                    .where(dataset.setid.isin([str(x) for x in setids]))
        if tags:
            await txn.exq(Query.from_(dataset_tag)
                          .where(dataset_tag.dataset_id.isin(subq))
                          .delete())

        if comments:
            await txn.exq(Query.from_(comment)
                          .where(comment.dataset_id.isin(subq))
                          .delete())

    @run_in_transaction
    async def delete_tag_values_without_ref(self, txn=None):
        await self._delete_values_without_ref('tag', 'dataset_tag', 'tag_id', txn)

    @run_in_transaction
    async def get_all_known_for_collection(self, collections, name, user, txn=None):
        collection_t = Table('collection')
        res = await txn.exq(self.get_actionable('collection', user, 'read')
                            .where(collection_t.name == name))
        if len(res) != 1:
            raise DBPermissionError
        collection = collections[name]
        descs = [x for x in collection.table_descriptors if x.through]
        all_known = {
            desc.key: [
                x['value'] for x in await txn.exq(Query.from_(desc.table).select('value'))
            ]
            for desc in descs
            if {'any', 'all'}.intersection(collection.filter_specs[desc.key].operators)
        }
        all_known.update({
            'f_status': list(STATUS),
            'f_tags': await self.get_all_known_tags_for_collection(collection.name),
        })
        return all_known

    @run_in_transaction
    async def get_all_known_tags_for_collection(self, collection_name, txn=None):
        collection, dataset, dataset_tag, tag = Tables('collection', 'dataset', 'dataset_tag',
                                                       'tag')
        query = Query.from_(tag)\
                     .select(tag.value)\
                     .where(tag.id.isin(Query.from_(dataset_tag)
                                        .join(dataset)
                                        .on(dataset_tag.dataset_id == dataset.id)
                                        .select(dataset_tag.tag_id)
                                        .join(collection)
                                        .on(dataset.collection_id == collection.id)
                                        .where(collection.name == collection_name)
                                        .distinct()))\
                     .orderby(tag.value)
        return [x['value'] for x in await txn.exq(query)]

    @staticmethod
    def get_listing_query(listing):
        listing, dataset, dataset_tag, tag = \
            Tables(listing, 'dataset', 'dataset_tag', 'tag')

        return Query.from_(listing)\
                    .join(dataset, how=JoinType.left_outer)\
                    .on(listing.id == dataset.id)\
                    .join(dataset_tag, how=JoinType.left_outer)\
                    .on(dataset.id == dataset_tag.dataset_id)\
                    .join(tag, how=JoinType.left_outer)\
                    .on(dataset_tag.tag_id == tag.id)\
                    .select(listing.id.as_('id'),
                            listing.row.as_('row'),
                            dataset.status.as_('status'),
                            GroupConcat(tag.value).as_('tag_value'))

    @staticmethod
    def try_extended_filter(query, name, value, operator, val_type, col):  # pylint: disable=unused-argument
        return False, query

    @staticmethod
    def postprocess_listing(rows):
        def fmt(row):
            if not row['tag_value']:
                return '[]'
            return json.dumps(sorted(row['tag_value'].split(',')))

        return [
            {
                'id': row['id'],
                'row': (row['row']
                        .replace('["#TAGS#"]', fmt(row))
                        .replace('"#TAGS#"', fmt(row)[1:-1] if fmt(row) != '[]' else '')
                        .replace('[,', '[')
                        .replace('"#STATUS#"', STATUS_STRS[row['status']])),
            }
            for row in rows
        ]

    @run_in_transaction
    async def get_filtered_listing(self, descs, filters, collection, user, txn=None):  # noqa: C901
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements,unused-argument
        listing, dataset, dataset_tag, tag = \
            Tables(descs[0].table, 'dataset', 'dataset_tag', 'tag')

        query = self.get_listing_query(descs[0].table)\
                    .where(dataset.discarded.ne(True)
                           & dataset.id.isin(self.get_actionable('dataset', user, 'list')))

        for name, value, operator, val_type in filters:
            if isinstance(value, int):
                value = min(value, sys.maxsize)

            if name == 'f_comments':
                comment = Table('comment')
                query = query.where(listing.id.isin(Query.from_(comment)
                                                    .select(comment.dataset_id)
                                                    .where(escaped_contains(comment.text, value))))
                continue

            if name == 'f_status':
                status_ids = list(STATUS.keys())
                bitmasks = [2**status_ids.index(x) for x in value]
                bitmask = sum(bitmasks)
                if operator == 'any':
                    query = query.where(dataset.status.bitwiseand(bitmask))

                elif operator == 'all':
                    query = query.where(dataset.status.bitwiseand(bitmask) == bitmask)

                else:
                    raise UnknownOperator(operator)

                continue

            if name == 'f_tags':
                if operator == 'any':
                    query = query.where(listing.id.isin(Query.from_(dataset_tag)
                                                        .join(tag)
                                                        .on(dataset_tag.tag_id == tag.id)
                                                        .where(tag.value.isin(value))
                                                        .select(dataset_tag.dataset_id)
                                                        .distinct()))

                elif operator == 'all':
                    query = query.where(listing.id.isin(Query.from_(dataset_tag)
                                                        .join(tag)
                                                        .on(dataset_tag.tag_id == tag.id)
                                                        .where(tag.value.isin(value))
                                                        .select(dataset_tag.dataset_id)
                                                        .groupby(dataset_tag.dataset_id)
                                                        .having(fn.Count('*') == len(value))))

                else:
                    raise UnknownOperator(operator)

                continue

            if val_type == 'datetime':
                if operator == 'eq':
                    field = getattr(listing, name)
                    query = query.where(field.between(value, value + 24 * 3600 * 1000 - 1))
                    continue

                if operator == 'ne':
                    field = getattr(listing, name)
                    query = query.where(~field.between(value, value + 24 * 3600 * 1000 - 1))
                    continue

                if operator in ['le', 'gt']:
                    value = value + 24 * 3600 * 1000 - 1

            extended_done, query = self.try_extended_filter(query, name, value, operator, val_type,
                                                            collection)
            if extended_done:
                continue

            field = getattr(listing, name)
            if operator == 'lt':
                query = query.where(field < value)

            elif operator == 'le':
                query = query.where(field <= value)

            elif operator == 'eq':
                query = query.where(field == value)

            elif operator == 'ne':
                query = query.where(field != value)

            elif operator == 'ge':
                query = query.where(field >= value)

            elif operator == 'gt':
                query = query.where(field > value)

            elif operator == 'substring':
                query = query.where(escaped_contains(field, value))

            elif operator == 'startswith':
                query = query.where(escaped_startswith(field, value))

            elif operator == 'any':
                desc = findfirst(lambda x, name=name: x.key == name, descs)
                rel = Table(desc.table)
                through = Table(desc.through)
                rel_id = getattr(through, desc.rel_id)
                listing_id = getattr(through, desc.listing_id)
                query = query.where(listing.id.isin(Query.from_(through)
                                                    .join(rel)
                                                    .on(rel_id == rel.id)
                                                    .where(rel.value.isin(value))
                                                    .select(listing_id)
                                                    .distinct()))

            elif operator == 'all':
                desc = findfirst(lambda x, name=name: x.key == name, descs)
                rel = Table(desc.table)
                through = Table(desc.through)
                rel_id = getattr(through, desc.rel_id)
                listing_id = getattr(through, desc.listing_id)
                query = query.where(listing.id.isin(Query.from_(through)
                                                    .join(rel)
                                                    .on(rel_id == rel.id)
                                                    .where(rel.value.isin(value))
                                                    .select(listing_id)
                                                    .groupby(listing_id)
                                                    .having(fn.Count('*') == len(value))))

            elif operator == 'substring_any':
                desc = findfirst(lambda x, name=name: x.key == name, descs)
                rel = Table(desc.table)
                through = Table(desc.through)
                rel_id = getattr(through, desc.rel_id)
                listing_id = getattr(through, desc.listing_id)
                query = query.where(listing.id.isin(Query.from_(through)
                                                    .join(rel)
                                                    .on(rel_id == rel.id)
                                                    .where(escaped_contains(rel.value, value))
                                                    .select(listing_id)
                                                    .distinct()))

            elif operator == 'words':
                for word in value:
                    query = query.where(escaped_contains(field, word))
            else:
                raise UnknownOperator(operator)

        query = query.orderby(tag.value).groupby('id')
        return self.postprocess_listing(await txn.exq(query))

    @run_in_transaction
    async def delete_listing_rel_values_without_ref(self, descs, txn=None):
        for desc in [y for x in descs.values() for y in x if y.through]:
            await self._delete_values_without_ref(desc.table, desc.through, desc.rel_id, txn)

    @run_in_transaction
    async def query(self, collections=None, discarded=None, outdated=None, path=None, tags=None,
                    abbrev=None, missing=None, txn=None):
        # pylint: disable=too-many-arguments, too-many-locals

        abbrev = 10 if abbrev is True else abbrev
        discarded = bool(discarded)

        dataset = Table('dataset')
        query = Query.from_(dataset)

        if collections:
            collection = Table('collection')
            query = query.join(collection)\
                         .on(dataset.collection_id == collection.id)\
                         .where(collection.name.isin(collections))

        if outdated:
            bitmask = ValueWrapper(STATUS_OUTDATED)
            query = query.where(dataset.status.bitwiseand(bitmask).eq(bitmask))

        query = query.where(dataset.discarded == discarded)

        if path or missing:
            files = Table('file')
            if path:
                query = query.where(dataset.id.isin(Query.from_(files)
                                                    .where(escaped_startswith(files.path, path))
                                                    .select(files.dataset_id)
                                                    .distinct()))
            if missing:
                query = query.where(dataset.id.isin(Query.from_(files)
                                                    .where(files.missing == missing)
                                                    .select(files.dataset_id)
                                                    .distinct()))

        if tags:
            tag = Table('tag')
            dataset_tag = Table('dataset_tag')
            query = query.where(dataset.id.isin(Query.from_(dataset_tag)
                                                .join(tag)
                                                .on(dataset_tag.tag_id == tag.id)
                                                .where(tag.value.isin(tags))
                                                .select(dataset_tag.dataset_id)
                                                .distinct()))

        query = query.select(dataset.setid)\
                     .orderby(dataset.setid)
        datasets = await txn.exq(query)
        return [
            x['setid'][:abbrev] if abbrev else x['setid']
            for x in datasets
        ]

    @run_in_transaction
    async def update_listing_relations(self, desc, values, relations, txn=None):
        await self._ensure_values(desc.table, values, None, txn)
        await self._ensure_refs(desc.table, desc.through, desc.rel_id, desc.listing_id, relations,
                                '::', None, txn=txn)

        table, through = Tables(desc.table, desc.through)
        relid = getattr(through, desc.rel_id)
        backid = getattr(through, desc.listing_id)
        await txn.exq(Query.from_(through)
                      .where(backid.isin({x[1] for x in relations})
                             & ~Tuple(relid, backid).isin(
                                 self.get_resolve_value_query(table, relations, '::', None)))
                      .delete())

    @run_in_transaction
    async def rpc_query(self, model, filters, attrs, order, limit, offset,  # noqa: C901
                        user, txn=None):
        # pylint: disable=too-many-arguments, too-many-statements, too-many-locals, too-many-branches
        result = {}
        if model.startswith('collection:'):
            name = f'l_{model[11:]}'
            table = Table(name)
            try:
                tablemeta = [x for x in self.listing_models if x._meta.table == name][0]._meta
            except IndexError:
                raise ValueError(f'there is no collection "{name}"')
        else:
            table = Table(model)
            try:
                tablemeta = [x for x in self.MODELS if x._meta.table == model][0]._meta
            except IndexError:
                raise ValueError(f'there is no model "{model}"')

        select = [
            getattr(table, k)
            for k, v in attrs.items()
            if v is True and k in tablemeta.db_fields
        ]
        if select:
            if 'id' not in attrs:
                select.append(table.id)
        else:
            select = [table.star]
        query = Query.from_(table).select(*select)

        try:
            for filt in filters:
                query = query.where(resolve_filter(table, filt, self.MODELS + self.listing_models))
        except FilterError as e:
            raise ValueError(*e.args)

        def customize_query(query, model, table, through=None):
            if model in ['collection', 'dataset']:
                if through:
                    query = query.where(through.isin(self.get_actionable(model, user, 'list')))
                else:
                    query = query.where(table.id.isin(self.get_actionable(model, user, 'list')))
            elif model in ['group', 'user'] and not through:
                query = query.where(table.name.not_like('marv:%'))
            return query

        query = customize_query(query, model, table)

        if order:
            if not isinstance(order, list) or len(order) != 2:
                raise ValueError(f'Order "{order}" should be ["fieldname", "ASC|DESC"]')
            query = query.orderby(getattr(table, order[0]),
                                  order=Order.desc if order[1] == 'DESC' else Order.asc)
        if limit:
            query = query.limit(limit)
            if offset:
                query = query.offset(offset)

        qres = cleanup_attrs(await txn.exq(query))
        result.setdefault(model, []).extend(qres)

        ids = [x['id'] for x in qres]
        for fieldname in set(attrs.keys()) - set(tablemeta.db_fields):
            requested = attrs[fieldname]
            if requested is True:
                select = ['*']
            else:
                select = [k for k, v in requested.items() if v is True]
                if 'id' not in select:
                    select.append('id')

            if model.startswith('collection:') and fieldname.startswith('dataset.'):
                modelfieldname = fieldname[8:]
                meta = [x for x in self.MODELS if x._meta.table == 'dataset'][0]._meta
            else:
                modelfieldname = fieldname
                meta = tablemeta

            if modelfieldname in meta.backward_fk_fields:
                field = meta.fields_map[modelfieldname]
                tablename = field.model_class._meta.table
                subtable = Table(tablename)
                if '*' not in select and field.relation_field not in select:
                    select.append(field.relation_field)
                query = Query.from_(subtable)\
                             .select(*select)\
                             .where(getattr(subtable, field.relation_field).isin(ids))
                query = customize_query(query, tablename, subtable)
                relres = await txn.exq(query)
                for prime in qres:
                    prime[fieldname] = [
                        x['id']
                        for x in relres
                        if x[field.relation_field] == prime['id']
                    ]
                if model.startswith('collection:'):
                    reskey = fieldname
                else:
                    reskey = tablename
                result.setdefault(reskey, []).extend(cleanup_attrs(relres))

            elif modelfieldname in meta.m2m_fields:
                field = meta.fields_map[modelfieldname]
                through = Table(field.through)
                tablename = field.model_class._meta.table
                rel = Table(tablename)
                query = Query.from_(through)\
                             .select(field.backward_key, field.forward_key)\
                             .where(getattr(through, field.backward_key).isin(ids))
                query = customize_query(query, field.through, through,
                                        getattr(through, field.forward_key))
                refs = await txn.exq(query)
                query = Query.from_(rel)\
                             .select(*select)\
                             .where(rel.id.isin({x[field.forward_key] for x in refs}))
                query = customize_query(query, tablename, rel)
                relres = await txn.exq(query)
                relids = [x['id'] for x in relres]
                for prime in qres:
                    prime[modelfieldname] = [
                        x[field.forward_key]
                        for x in refs
                        if x[field.backward_key] == prime['id'] and x[field.forward_key] in relids
                    ]
                if model.startswith('collection:'):
                    reskey = fieldname
                else:
                    reskey = tablename
                result.setdefault(reskey, []).extend(cleanup_attrs(relres))

            else:
                raise ValueError(f'Field {modelfieldname!r} not on model {model!r}')

        return result

    @classmethod
    def check_db_version(cls, dburi, missing_ok=False):
        dbpath = Path(dburi.split('sqlite://', 1)[1])
        if not dbpath.exists():
            if not missing_ok:
                raise DBNotInitialized('There is no marv database.')
            return

        metadata = Table('metadata')
        required = cls.VERSION
        try:
            conn = sqlite3.connect(f'file:{dbpath}?mode=ro', uri=True)
            with conn:
                have = conn.execute(Query.from_(metadata)
                                    .select(metadata.value)
                                    .where(metadata.key == 'database_version')
                                    .get_sql())\
                           .fetchone()[0]
                if have != required:
                    raise DBVersionError(
                        f'DB version on disk "{have}", but "{required}" required.',
                    )
        except (sqlite3.OperationalError, TypeError):
            raise DBVersionError(
                'DB version is unknown, metadata table or version entry missing.',
            )
        finally:
            conn.close()

    async def restore_database(self, site, dct):
        async with scoped_session(self) as txn:
            for keys, handler in self.IMPORT_HANDLERS:
                if keys.issubset(dct.keys()):
                    await handler(site, dct, txn)
            dct.pop('version', None)
            if dct:
                log.warning(
                    'Some fields from the dump file could not be imported. If you are imporing '
                    'from a newer version of MARV of from a different MARV distribution (EE into '
                    'CE) this behavior is expected. Please be aware that some information from '
                    'the original dump was lost. The following fields were not processed:\n %s',
                    list(dct.keys()),
                )

    @classmethod
    async def dump_database(cls, dburi):
        """Dump database.

        The structure of the database is reflected and therefore also
        older databases, not matching the current version of marv, can be
        dumped.
        """
        cls.check_db_version(dburi)

        class T2(Tortoise):
            apps = {}
            _connections = {}
            _inited = False

            @classmethod
            async def transaction(cls):
                await cls.init(db_url=dburi, modules={'models': []})
                connection = cls._connections['default']
                return connection._in_transaction()  # pylint: disable=protected-access

        dump = {'version': Database.DUMP_VERSION}
        async with await T2.transaction() as txn:
            master = Table('sqlite_master')
            tables = {
                x['name']: Table(x['name'])
                for x in await get_items_for_query(
                    Query.from_(master)
                    .select(master.name)
                    .where((master.type == 'table')
                           & escaped_not_startswith(master.name, 'sqlite_')
                           & escaped_not_startswith(master.name, 'l_')),
                    txn,
                )
            }

            for tbls, dumper in cls.EXPORT_HANDLERS:
                assert tbls.issubset(tables.keys()), tbls
                await dumper(tables, dump, txn)
            assert not tables, tables.keys()

        await T2.close_connections()
        return dump
