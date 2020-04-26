# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=too-many-lines

import asyncio
import hashlib
import secrets
import string
import sys
from collections import namedtuple
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime
from functools import reduce
from itertools import groupby, product
from logging import getLogger

import bcrypt
from pypika import JoinType, Order, SQLLiteQuery as Query, Table, Tables, Tuple, functions as fn
from pypika.terms import AggregateFunction, Criterion, EmptyCriterion, ValueWrapper
from tortoise import Tortoise
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.transactions import current_transaction_map

from marv_node.setid import SetID
from . import utils
from .model import Group, Leaf, User
from .model import STATUS, STATUS_MISSING, STATUS_OUTDATED
from .model import __models__ as MODELS
from .utils import findfirst


log = getLogger(__name__)


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


@asynccontextmanager
async def scoped_session(database, transaction=None):
    """Transaction scope for database operations."""
    if transaction:
        yield transaction
    else:
        connection = await database.connection_queue.get()
        try:
            # pylint: disable=protected-access
            async with connection._in_transaction() as transaction:
                async def exq(query, count=False):
                    cnt, res = await transaction.execute_query(query.get_sql())
                    return cnt if count else res
                transaction.exq = exq
                yield transaction
        finally:
            await database.connection_queue.put(connection)


def run_in_transaction(func):
    async def wrapper(database, *args, transaction=None, **kwargs):
        async with scoped_session(database, transaction=transaction) as transaction:
            return await func(database, *args, transaction=transaction, **kwargs)

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
        return f'(VALUES {",".join(x.get_sql(**kw) for x in self.values)})'


class GroupConcat(AggregateFunction):
    def __init__(self, term, alias=None):
        super().__init__('GROUP_CONCAT', term, alias=alias)


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


def get_resolve_value_query(rel, relations):
    out, tmp = Tables('out', 'tmp')  # pylint: disable=unbalanced-tuple-unpacking
    return Query.with_(Query.with_(Query.from_(ValuesTuple(*relations))
                                   .select('*'), 'tmp(value, back_id)')
                       .from_(tmp)
                       .join(rel)
                       .on(tmp.value == rel.value)
                       .select(rel.id, tmp.back_id), 'out(rel_id, back_id)')\
                .from_(out)\
                .select(out.rel_id, out.back_id)


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


def resolve_filter(table, fltr):  # noqa: C901
    if not isinstance(fltr, dict):
        raise FilterError(f'Expected dict not {fltr!r}')

    operator = fltr.get('op')
    if not operator:
        raise FilterError(f"Missing 'op' in {fltr!r}")
    if not isinstance(operator, str):
        raise FilterError(f'Expected string not {operator!r}')

    value = fltr.get('value')
    name = fltr.get('name')
    tablemeta = findfirst(lambda x: x._meta.table == table._table_name, MODELS)._meta

    if operator == 'and':
        return reduce(lambda x, y: x & resolve_filter(table, y), value, EmptyCriterion())
    if operator == 'or':
        return reduce(lambda x, y: x | resolve_filter(table, y), value, EmptyCriterion())
    if operator == 'not':
        return resolve_filter(table, value).negate()

    if not isinstance(name, str):
        raise FilterError(f"Missing 'name' in {fltr!r}")

    if '.' in name:
        fieldname, subname = name.split('.', 1)
        if fieldname in tablemeta.backward_fk_fields:
            field = tablemeta.fields_map[fieldname]
            subtable = Table(field.model_class._meta.table)
            resolved = resolve_filter(subtable, {'op': operator, 'name': subname, 'value': value})
            return getattr(table, 'id').isin(Query.from_(subtable)
                                             .select(getattr(subtable, field.relation_field))
                                             .where(resolved))

        if fieldname in tablemeta.m2m_fields:
            field = tablemeta.fields_map[fieldname]
            through = Table(field.through)
            rel = Table(field.model_class._meta.table)
            resolved = resolve_filter(rel, {'op': operator, 'name': subname, 'value': value})
            return getattr(table, 'id').isin(Query.from_(through)
                                             .join(rel)
                                             .on(getattr(through, field.forward_key) == rel.id)
                                             .where(resolved)
                                             .select(getattr(through, field.backward_key))
                                             .distinct())

        raise FilterError(f'Field {fieldname!r} not on model {tablemeta.table}')

    if name not in tablemeta.db_fields:
        raise FilterError(f'Field {name!r} not on model {tablemeta.table}')

    if operator not in OPS:
        raise FilterError(f'Unknown operator {operator!r}')

    field = getattr(table, name)
    return OPS[operator](field, value)


def cleanup_attrs(items):
    return [
        {k: x[k] for k in x.keys() if k != 'password'}
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


def id_crit(ids):
    dataset = Table('dataset')
    return dataset.id.isin(ids)


def setid_crit(ids):
    dataset = Table('dataset')
    return dataset.setid.isin([str(x) for x in ids])


class Database:
    # pylint: disable=too-many-public-methods
    def __init__(self):
        self.connections = []
        self.connection_queue = asyncio.Queue()

    async def initialize_connections(self):
        defcon = Tortoise.get_connection('default')
        for idx in range(48):
            name = f'connection_{idx}'
            db_params = defcon.pragmas.copy()
            db_params['connection_name'] = name
            connection = defcon.__class__(defcon.filename, **db_params)
            await connection.create_connection(with_db=True)
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
    async def authenticate(self, username, password, transaction=None):
        if not username or not password:
            return False
        try:
            user = await User.get(name=username, realm='marv').using_db(transaction)
        except DoesNotExist:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))

    @run_in_transaction
    async def bulk_um(self, users_add, users_remove, groups_add, groups_remove,
                      groups_add_users, groups_remove_users, transaction=None):
        # pylint: disable=too-many-arguments

        for name in users_remove:
            await User.get(name=name).using_db(transaction).delete()

        for name in users_add:
            await User.create(name=name, realm='marv', using_db=transaction)

        for name in groups_remove:
            await Group.get(name=name).using_db(transaction).delete()

        for name in groups_add:
            await Group.create(name=name, using_db=transaction)

        for name, users in groups_remove_users:
            group = await Group.get(name=name).using_db(transaction)
            users = await User.filter(name__in=users).using_db(transaction)
            await group.users.remove(*users, using_db=transaction)

        for name, users in groups_add_users:
            group = await Group.get(name=name).using_db(transaction)
            users = await User.filter(name__in=users).using_db(transaction)
            await group.users.add(*users, using_db=transaction)

    @run_in_transaction
    async def user_add(self, name, password, realm, realmuid, given_name=None, family_name=None,
                       email=None, time_created=None, time_updated=None, _restore=None,
                       transaction=None):
        # pylint: disable=too-many-arguments
        if not _restore and password is not None:
            password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        now = datetime.utcnow()  # noqa: DTZ
        time_created = datetime.fromtimestamp(time_created) if time_created else now
        time_updated = datetime.fromtimestamp(time_updated) if time_updated else now
        try:
            user = await User.create(name=name, password=password, realm=realm,
                                     given_name=given_name, family_name=family_name,
                                     email=email, realmuid=realmuid, time_created=time_created,
                                     time_updated=time_updated, using_db=transaction)
            if _restore:
                user = Table('user')
                await transaction.exq(Query.update(user)
                                      .set(user.time_updated, time_updated)
                                      .where(user.name == name))
        except IntegrityError:
            raise ValueError(f'User {name} exists already')
        return user

    @run_in_transaction
    async def user_rm(self, username, transaction=None):
        try:
            user = await User.get(name=username).using_db(transaction)
            await user.delete(using_db=transaction)
        except DoesNotExist:
            raise ValueError(f'User {username} does not exist')

    @run_in_transaction
    async def user_pw(self, username, password, transaction=None):
        try:
            user = await User.get(name=username).using_db(transaction)
        except DoesNotExist:
            raise ValueError(f'User {username} does not exist')

        user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user.time_updated = int(utils.now())
        await user.save(using_db=transaction)

    @run_in_transaction
    async def group_add(self, groupname, transaction=None):
        try:
            await Group.create(name=groupname, using_db=transaction)
        except IntegrityError:
            raise ValueError(f'Group {groupname} exists already')

    @run_in_transaction
    async def group_rm(self, groupname, transaction=None):
        try:
            group = await Group.get(name=groupname).using_db(transaction)
            await group.delete(using_db=transaction)
        except DoesNotExist:
            raise ValueError(f'Group {groupname} does not exist')

    @run_in_transaction
    async def group_adduser(self, groupname, username, transaction=None):
        try:
            group = await Group.get(name=groupname).using_db(transaction)
        except DoesNotExist:
            raise ValueError(f'Group {groupname} does not exist')
        try:
            user = await User.get(name=username).using_db(transaction)
        except DoesNotExist:
            raise ValueError(f'User {username} does not exist')
        await group.users.add(user, using_db=transaction)

    @run_in_transaction
    async def group_rmuser(self, groupname, username, transaction=None):
        try:
            group = await Group.get(name=groupname).using_db(transaction)
        except DoesNotExist:
            raise ValueError(f'Group {groupname} does not exist')
        try:
            user = await User.get(name=username).using_db(transaction)
        except DoesNotExist:
            raise ValueError(f'User {username} does not exist')
        await group.users.remove(user, using_db=transaction)

    @run_in_transaction
    async def get_users(self, deep=False, transaction=None):
        query = User.all().using_db(transaction).order_by('name')
        if deep:
            query = query.prefetch_related('groups')
        return await query

    @run_in_transaction
    async def get_user_by_name(self, name, deep=False, transaction=None):
        query = User.filter(name=name).using_db(transaction)
        if deep:
            query = query.prefetch_related('groups')
        return await query.first()

    @run_in_transaction
    async def get_user_by_realmuid(self, realm, realmuid, deep=False, transaction=None):
        query = User.filter(realm=realm, realmuid=realmuid).using_db(transaction)
        if deep:
            query = query.prefetch_related('groups')
        return await query.first()

    @run_in_transaction
    async def get_groups(self, deep=False, transaction=None):
        query = Group.all().using_db(transaction).order_by('name')
        if deep:
            query = query.prefetch_related('users')
        return await query

    @run_in_transaction
    async def leaf_add(self, name, access_token=None, refresh_token=None, time_created=None,
                       time_updated=None, _restore=None, transaction=None):
        # pylint: disable=too-many-arguments
        if _restore:
            clear_access_token = None
            clear_refresh_token = None
        else:
            alnum = string.ascii_letters + string.digits
            clear_access_token = ''.join(secrets.choice(alnum) for i in range(20))
            clear_refresh_token = ''.join(secrets.choice(alnum) for i in range(20))
            access_token = hashlib.sha256(clear_access_token.encode()).hexdigest()
            refresh_token = hashlib.sha256(clear_refresh_token.encode()).hexdigest()

        now = datetime.utcnow()  # noqa: DTZ
        time_created = datetime.fromtimestamp(time_created) if time_created else now
        time_updated = datetime.fromtimestamp(time_updated) if time_updated else now
        try:
            leaf = await Leaf.create(name=name, access_token=access_token,
                                     refresh_token=refresh_token, time_created=time_created,
                                     time_updated=time_updated, using_db=transaction)
            if _restore:
                leaf_t = Table('leaf')
                await transaction.exq(Query.update(leaf_t)
                                      .set(leaf_t.time_updated, time_updated)
                                      .where(leaf_t.name == name))
        except IntegrityError:
            raise ValueError(f'Recording unit {name} exists already')

        return leaf

    @run_in_transaction
    async def leaf_regentoken(self, name, transaction=None):
        try:
            leaf = await Leaf.get(name=name).using_db(transaction)
        except DoesNotExist:
            raise ValueError(f'Recording unit {name} does not exist')

        alnum = string.ascii_letters + string.digits
        clear_access_token = ''.join(secrets.choice(alnum) for i in range(20))
        clear_refresh_token = ''.join(secrets.choice(alnum) for i in range(20))
        leaf.access_token = hashlib.sha256(clear_access_token.encode('utf8')).hexdigest()
        leaf.refresh_token = hashlib.sha256(clear_refresh_token.encode('utf8')).hexdigest()
        leaf.time_updated = int(utils.now())
        await leaf.save(using_db=transaction)
        leaf.clear_access_token = clear_access_token
        leaf.clear_refresh_token = clear_refresh_token
        return leaf

    @run_in_transaction
    async def get_leafs(self, transaction=None):
        return await Leaf.all().using_db(transaction).order_by('name')

    @run_in_transaction
    async def get_leaf_by_token(self, clear_access_token, transaction=None):
        access_token = hashlib.sha256(clear_access_token.encode()).hexdigest()
        return await Leaf.filter(access_token=access_token).using_db(transaction).first()

    @run_in_transaction
    async def resolve_shortids(self, prefixes, discarded=False, transaction=None):
        setids = set()
        dataset = Table('dataset')
        for prefix in prefixes:
            if isinstance(prefix, SetID):
                prefix = str(prefix)

            setid = await transaction.exq(Query.from_(dataset)
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

    async def _get_datasets_by_id_crit(self, crit, prefetch, transaction):
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
        items = await transaction.exq(query)
        return modelize(items, prefetch)

    @run_in_transaction
    async def get_datasets_by_setids(self, setids, prefetch, transaction=None):
        return await self._get_datasets_by_id_crit(setid_crit(setids), prefetch, transaction)

    @run_in_transaction
    async def get_datasets_by_dbids(self, ids, prefetch, transaction=None):
        return await self._get_datasets_by_id_crit(id_crit(ids), prefetch, transaction)

    @run_in_transaction
    async def get_filepath_by_setid_idx(self, setid, idx, transaction=None):
        dataset, file = Tables('dataset', 'file')
        return (await transaction.exq(Query.from_(file)
                                      .join(dataset)
                                      .on(file.dataset_id == dataset.id)
                                      .where((file.idx == idx) & (dataset.setid == str(setid)))
                                      .select('path')))[0]['path']

    @run_in_transaction
    async def get_datasets_for_collections(self, collections, transaction=None):
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
        return [SetID(x['setid']) for x in await transaction.exq(query)]

    async def _set_dataset_discarded_by_id_crit(self, crit, state, transaction):
        dataset = Table('dataset')
        await transaction.exq(Query.update(dataset)
                              .set(dataset.discarded, state)
                              .where(crit))

    @run_in_transaction
    async def discard_datasets_by_setids(self, setids, state=True, transaction=None):
        await self._set_dataset_discarded_by_id_crit(setid_crit(setids), state, transaction)

    @run_in_transaction
    async def discard_datasets_by_dbids(self, ids, state=True, transaction=None):
        await self._set_dataset_discarded_by_id_crit(id_crit(ids), state, transaction)

    @run_in_transaction
    async def cleanup_discarded(self, descs, transaction=None):
        collection, dataset = Tables('collection', 'dataset')
        datasets = await transaction.exq(Query.from_(dataset)
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
            await transaction.exq(Query.from_(dataset)
                                  .where(dataset.id.isin(ids))
                                  .delete())

            for table in (Table('dataset_tag'), Table('comment'), Table('file')):
                await transaction.exq(Query.from_(table)
                                      .where(table.dataset_id.isin(ids))
                                      .delete())

            tbls = descs[col]
            assert not tbls[0].through, 'Listing table should be first'
            listing = Table(tbls[0].table)

            await transaction.exq(Query.from_(listing)
                                  .where(listing.id.isin(ids))
                                  .delete())

            for desc in [x for x in tbls if x.through]:
                through = Table(desc.through)
                id_field = getattr(through, desc.listing_id)
                await transaction.exq(Query.from_(through)
                                      .where(id_field.isin(ids))
                                      .delete())

    @run_in_transaction
    async def bulk_comment(self, comments, transaction=None):
        comment, dataset, tmp, user = Tables('comment', 'dataset', 'tmp', 'user')
        comments = [(x['dataset_id'], x['author'], x['time_added'], x['text']) for x in comments]
        query = Query.into(comment)\
                     .columns('dataset_id', 'author', 'time_added', 'text')\
                     .from_(Query.with_(Query.from_(ValuesTuple(*comments))
                                        .select('*'), 'tmp(dataset_id, author, time_added, text)')
                            .from_(tmp)
                            .join(dataset)
                            .on(tmp.dataset_id == dataset.id)
                            .join(user)
                            .on(tmp.author == user.name)
                            .select(tmp.star))\
                     .select('*')
        count = await transaction.exq(query, count=True)
        if count != len(comments):
            raise DBError('Bulk commenting failed, users or datasets missing')

    @run_in_transaction
    async def comment_by_setids(self, setids, author, text, transaction=None):
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
        count = await transaction.exq(query, count=True)
        if count != len(setids):
            raise DBError(f'Commenting failed. User {author!r} or one of the datasets are missing')

    @run_in_transaction
    async def delete_comments_by_ids(self, ids, transaction=None):
        comment = Table('comment')
        await transaction.exq(Query.from_(comment)
                              .where(comment.id.isin(ids))
                              .delete())

    @run_in_transaction
    async def get_comments_by_setids(self, setids, transaction=None):
        comment, dataset = Tables('comment', 'dataset')
        if setids:
            crit = dataset.setid.isin([str(x) for x in setids])
        else:
            crit = dataset.discarded.ne(True)
        query = Query.from_(comment)\
                     .join(dataset).on(comment.dataset_id == dataset.id)\
                     .select(comment.star, dataset.star)\
                     .where(crit)
        items = await transaction.exq(query)
        return modelize(items, ['dataset'])

    async def _ensure_values(self, tablename, values, transaction):
        table = Table(tablename)
        query = Query.into(table)\
                     .columns('value')\
                     .from_(FromExceptQuery
                            .from_(Query.from_(ValuesTuple(*values)).select('*'))
                            .except_(Query().from_(table).select(table.value)))\
                     .select('*')
        await transaction.exq(query)

    async def _ensure_refs(self, relname, throughname, rel_id, back_id, relations, transaction):
        # pylint: disable=too-many-arguments
        rel, through = Tables(relname, throughname)
        relid = getattr(through, rel_id)
        backid = getattr(through, back_id)
        query = Query.into(through)\
                     .columns(rel_id, back_id)\
                     .from_(FromExceptQuery
                            .from_(get_resolve_value_query(rel, relations))
                            .except_(Query.from_(through).select(relid, backid)))\
                     .select('*')
        await transaction.exq(query)

    async def _delete_values_without_ref(self, relname, throughname, rel_id, transaction=None):
        rel, through = Tables(relname, throughname)
        await transaction.exq(Query.from_(rel)
                              .where(rel.id.notin(Query.from_(throughname)
                                                  .select(getattr(through, rel_id))
                                                  .distinct()))
                              .delete())

    @run_in_transaction
    async def bulk_tag(self, add, remove, transaction=None):
        if add:
            await self._ensure_values('tag', [(x[0],) for x in add], transaction)
            await self._ensure_refs('tag', 'dataset_tag', 'tag_id', 'dataset_id', add,
                                    transaction)

        if remove:
            through, tag = Tables('dataset_tag', 'tag')
            await transaction.exq(Query.from_(through)
                                  .delete()
                                  .select(through.tag_id, through.dataset_id)
                                  .where(Tuple(through.tag_id, through.dataset_id)
                                         .isin(get_resolve_value_query(tag, remove))))

    @run_in_transaction
    async def update_tags_by_setids(self, setids, add, remove, transaction=None):
        setids = [str(x) for x in setids]
        dataset = Table('dataset')
        colids = await transaction.exq(Query.from_(dataset)
                                       .where(dataset.setid.isin(setids))
                                       .select(dataset.id))
        add = [(tag, colid['id']) for tag, colid in product(add, colids)]
        remove = [(tag, colid['id']) for tag, colid in product(remove, colids)]
        await self.bulk_tag(add, remove, transaction=transaction)

    @run_in_transaction
    async def list_tags(self, collections=None, transaction=None):
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

        return [x['value'] for x in await transaction.exq(query)]

    @run_in_transaction
    async def delete_comments_tags(self, setids, comments, tags, transaction=None):
        dataset, dataset_tag, comment = Tables('dataset', 'dataset_tag', 'comment')
        subq = Query.from_(dataset)\
                    .select(dataset.id)\
                    .where(dataset.setid.isin([str(x) for x in setids]))
        if tags:
            await transaction.exq(Query.from_(dataset_tag)
                                  .where(dataset_tag.dataset_id.isin(subq))
                                  .delete())

        if comments:
            await transaction.exq(Query.from_(comment)
                                  .where(comment.dataset_id.isin(subq))
                                  .delete())

    @run_in_transaction
    async def delete_tag_values_without_ref(self, transaction=None):
        await self._delete_values_without_ref('tag', 'dataset_tag', 'tag_id', transaction)

    @run_in_transaction
    async def get_all_known_for_collection(self, collection, transaction=None):
        descs = [x for x in collection.table_descriptors if x.through]
        all_known = {
            desc.key: [
                x['value'] for x in await transaction.exq(Query.from_(desc.table).select('value'))
            ]
            for desc in descs
            if {'any', 'all'}.intersection(collection.filter_specs[desc.key].operators)
        }
        all_known.update({
            'status': list(STATUS),
            'tags': await self.get_all_known_tags_for_collection(collection.name),
        })
        return all_known

    @run_in_transaction
    async def get_all_known_tags_for_collection(self, collection_name, transaction=None):
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
        return [x['value'] for x in await transaction.exq(query)]

    @run_in_transaction  # noqa: C901
    async def get_filtered_listing(self, descs, filters, transaction=None):  # noqa: C901
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        listing, dataset, dataset_tag, tag = \
            Tables(descs[0].table, 'dataset', 'dataset_tag', 'tag')

        query = Query.from_(listing)\
                     .join(dataset, how=JoinType.left_outer)\
                     .on(listing.id == dataset.id)\
                     .join(dataset_tag, how=JoinType.left_outer)\
                     .on(dataset.id == dataset_tag.dataset_id)\
                     .join(tag, how=JoinType.left_outer)\
                     .on(dataset_tag.tag_id == tag.id)\
                     .select(listing.id.as_('id'),
                             listing.row.as_('row'),
                             dataset.status.as_('status'),
                             GroupConcat(tag.value).as_('tag_value'))\
                     .where(dataset.discarded.ne(True))

        for name, value, operator, val_type in filters:
            if isinstance(value, int):
                value = min(value, sys.maxsize)

            if name == 'comments':
                comment = Table('comment')
                query = query.where(listing.id.isin(Query.from_(comment)
                                                    .select(comment.dataset_id)
                                                    .where(escaped_contains(comment.text, value))))
                continue

            if name == 'status':
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

            if name == 'tags':
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
        return await transaction.exq(query)

    @run_in_transaction
    async def delete_listing_rel_values_without_ref(self, descs, transaction=None):
        for desc in [y for x in descs.values() for y in x if y.through]:
            await self._delete_values_without_ref(desc.table, desc.through, desc.rel_id,
                                                  transaction)

    @run_in_transaction
    async def query(self, collections=None, discarded=None, outdated=None, path=None, tags=None,
                    abbrev=None, missing=None, transaction=None):
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
        datasets = await transaction.exq(query)
        return [
            x['setid'][:abbrev] if abbrev else x['setid']
            for x in datasets
        ]

    @run_in_transaction
    async def update_listing_relations(self, desc, values, relations, transaction=None):
        await self._ensure_values(desc.table, values, transaction)
        await self._ensure_refs(desc.table, desc.through, desc.rel_id, desc.listing_id, relations,
                                transaction=transaction)

        table, through = Tables(desc.table, desc.through)
        relid = getattr(through, desc.rel_id)
        backid = getattr(through, desc.listing_id)
        await transaction.exq(Query.from_(through)
                              .where(backid.isin({x[1] for x in relations})
                                     & ~Tuple(relid, backid).isin(
                                         get_resolve_value_query(table, relations)))
                              .delete())

    @run_in_transaction  # noqa: C901
    async def rpc_query(self, model, filters, attrs, order, limit, offset,  # noqa: C901
                        transaction=None):
        # pylint: disable=too-many-arguments, too-many-statements, too-many-locals, too-many-branches
        result = {}
        table = Table(model)
        try:
            tablemeta = [x for x in MODELS if x._meta.table == model][0]._meta
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

        for filt in filters:
            query = query.where(resolve_filter(table, filt))

        if order:
            if not isinstance(order, list) or len(order) != 2:
                raise ValueError(f'Order "{order}" should be ["fieldname", "ASC|DESC"]')
            query = query.orderby(getattr(table, order[0]),
                                  order=Order.desc if order[1] == 'DESC' else Order.asc)
        if limit:
            query = query.limit(limit)
            if offset:
                query = query.offset(offset)

        qres = cleanup_attrs(await transaction.exq(query))
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

            if fieldname in tablemeta.backward_fk_fields:
                field = tablemeta.fields_map[fieldname]
                tablename = field.model_class._meta.table
                subtable = Table(tablename)
                if '*' not in select and field.relation_field not in select:
                    select.append(field.relation_field)
                query = Query.from_(subtable)\
                             .select(*select)\
                             .where(getattr(subtable, field.relation_field).isin(ids))
                relres = await transaction.exq(query)
                for prime in qres:
                    prime[fieldname] = [
                        x['id']
                        for x in relres
                        if x[field.relation_field] == prime['id']
                    ]
                result.setdefault(tablename, []).extend(cleanup_attrs(relres))

            elif fieldname in tablemeta.m2m_fields:
                field = tablemeta.fields_map[fieldname]
                through = Table(field.through)
                tablename = field.model_class._meta.table
                rel = Table(tablename)
                query = Query.from_(through)\
                             .select(field.backward_key, field.forward_key)\
                             .where(getattr(through, field.backward_key).isin(ids))
                refs = await transaction.exq(query)
                for prime in qres:
                    prime[fieldname] = [
                        x[field.forward_key]
                        for x in refs
                        if x[field.backward_key] == prime['id']
                    ]
                query = Query.from_(rel)\
                             .select(*select)\
                             .where(rel.id.isin({x[field.forward_key] for x in refs}))
                relres = await transaction.exq(query)
                result.setdefault(tablename, []).extend(cleanup_attrs(relres))

            else:
                raise ValueError(f'field {fieldname} not on model {model}')

        return result


def dt_to_sec(dtime):
    """Return seconds since epoch for datetime object."""
    sec = (datetime.fromisoformat(dtime) - datetime.fromtimestamp(0)).total_seconds()  # noqa: DTZ
    return int(sec)


async def dump_database(dburi):  # noqa: C901
    """Dump database.

    The structure of the database is reflected and therefore also
    older databases, not matching the current version of marv, can be
    dumped.
    """
    # pylint: disable=too-many-locals,too-many-statements

    class T2(Tortoise):
        apps = {}
        _connections = {}
        _inited = False

        @classmethod
        async def transaction(cls):
            await cls.init(db_url=dburi, modules={'models': []})
            connection = cls._connections['default']
            return connection._in_transaction()  # pylint: disable=protected-access

    async with await T2.transaction() as conn:
        async def get_items_for_query(query):
            return [
                {k: x[k] for k in x.keys()}
                for x in (await conn.execute_query(query.get_sql()))[1]
            ]
        master = Table('sqlite_master')
        tables = {
            x['name']: Table(x['name'])
            for x in await get_items_for_query(
                Query.from_(master)
                .select(master.name)
                .where((master.type == 'table')
                       & escaped_not_startswith(master.name, 'sqlite_')
                       & escaped_not_startswith(master.name, 'l_')),
            )
        }

        comments = {}
        comment_t = tables.pop('comment')
        items = await get_items_for_query(Query.from_(comment_t)
                                          .select(comment_t.star)
                                          .orderby(comment_t.dataset_id)
                                          .orderby(comment_t.id))
        for did, grp in groupby(items, key=lambda x: x['dataset_id']):
            assert did not in comments
            comments[did] = lst = []
            for comment in grp:
                # Everything except these fields is included in the dump
                del comment['dataset_id']
                del comment['id']
                lst.append(comment)

        files = {}
        file_t = tables.pop('file')
        items = await get_items_for_query(Query.from_(file_t)
                                          .select(file_t.star)
                                          .orderby(file_t.dataset_id)
                                          .orderby(file_t.id))
        for did, grp in groupby(items, key=lambda x: x['dataset_id']):
            assert did not in files
            files[did] = lst = []
            for file in grp:
                # Everything except these fields is included in the dump
                del file['id']
                del file['dataset_id']
                del file['idx']
                lst.append(file)

        tags = {}
        dataset_tag_t = tables.pop('dataset_tag')
        tag_t = tables.pop('tag')
        items = await get_items_for_query(Query.from_(dataset_tag_t)
                                          .join(tag_t)
                                          .on(dataset_tag_t.tag_id == tag_t.id)
                                          .select('*')
                                          .orderby(dataset_tag_t.dataset_id)
                                          .orderby(tag_t.value))
        for did, grp in groupby(items, key=lambda x: x['dataset_id']):
            assert did not in tags
            tags[did] = lst = []
            for tag in grp:
                del tag['dataset_id']
                del tag['id']
                del tag['tag_id']
                lst.append(tag.pop('value'))
                assert not tag

        dump = {}
        dump['datasets'] = collections = {}
        collection = tables.pop('collection')
        dataset_t = tables.pop('dataset')
        items = await get_items_for_query(Query.from_(dataset_t)
                                          .join(collection)
                                          .on(dataset_t.collection_id == collection.id)
                                          .select(dataset_t.star, collection.name.as_('collection'))
                                          .orderby(dataset_t.setid))
        for dataset in items:
            did = dataset.pop('id')  # Everything except this is included in the dump
            del dataset['collection_id']
            dataset['comments'] = comments.pop(did, [])
            dataset['files'] = files.pop(did)
            dataset['tags'] = tags.pop(did, [])
            collections.setdefault(dataset.pop('collection'), []).append(dataset)

        assert not comments, comments
        assert not files, files
        assert not tags, tags

        groups = {}
        group_t = tables.pop('group')
        user_group_t = tables.pop('user_group')
        items = await get_items_for_query(Query.from_(user_group_t)
                                          .join(group_t)
                                          .on(user_group_t.group_id == group_t.id)
                                          .select('*')
                                          .orderby(user_group_t.user_id)
                                          .orderby(group_t.name))
        for uid, grp in groupby(items, key=lambda x: x['user_id']):
            assert uid not in groups
            groups[uid] = lst = []
            for group in grp:
                del group['user_id']
                del group['group_id']
                del group['id']
                name = group.pop('name')
                assert not group
                lst.append(name)

        dump['users'] = users = []
        user_t = tables.pop('user')
        items = await get_items_for_query(Query.from_(user_t)
                                          .select('*')
                                          .orderby(user_t.name))
        for user in items:
            user_id = user.pop('id')  # Everything except this is included in the dump
            user['groups'] = groups.pop(user_id, [])
            user['time_created'] = dt_to_sec(user['time_created'])
            user['time_updated'] = dt_to_sec(user['time_updated'])
            users.append(user)

        dump['leafs'] = leafs = []
        if 'leaf' in tables:
            leaf_t = tables.pop('leaf')
            items = await get_items_for_query(Query.from_(leaf_t)
                                              .select('*')
                                              .orderby(leaf_t.name))
            for leaf in items:
                del leaf['id']
                leaf['time_created'] = dt_to_sec(leaf['time_created'])
                leaf['time_updated'] = dt_to_sec(leaf['time_updated'])
                leafs.append(leaf)

        assert not groups, groups
        assert not tables, tables.keys()

    await T2.close_connections()
    return dump
