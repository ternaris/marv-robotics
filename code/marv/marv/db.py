# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=too-many-lines

import asyncio
import sys
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
from .model import Comment, Dataset, File, Group, Tag, User
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
                yield transaction
        finally:
            await database.connection_queue.put(connection)


def run_in_transaction(func):
    async def wrapper(database, *args, transaction=None, **kwargs):
        async with scoped_session(database, transaction=transaction) as transaction:
            return await func(database, *args, transaction=transaction, **kwargs)

    return wrapper


class GroupConcat(AggregateFunction):
    def __init__(self, term, alias=None):
        super().__init__('GROUP_CONCAT', term, alias=alias)


class EscapableLikeCriterion(Criterion):
    def __init__(self, left, right, escchr, alias=None):
        super().__init__(alias)
        self.left = left
        self.right = right
        self.escchr = escchr

    def fields(self):
        return self.left.fields() + self.right.fields()

    def get_sql(self, with_alias=False, **kwargs):  # pylint: disable=arguments-differ
        sql = (f'{self.left.get_sql(**kwargs)} LIKE {self.right.get_sql(**kwargs)} '
               f'ESCAPE "{self.escchr}"')
        if with_alias and self.alias:
            return f'{sql} "{self.alias}"'
        return sql


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
            subtable = Table(field.type._meta.table)
            resolved = resolve_filter(subtable, {'op': operator, 'name': subname, 'value': value})
            return getattr(table, 'id').isin(Query.from_(subtable)
                                             .select(getattr(subtable, field.relation_field))
                                             .where(resolved))

        if fieldname in tablemeta.m2m_fields:
            field = tablemeta.fields_map[fieldname]
            through = Table(field.through)
            rel = Table(field.type._meta.table)
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
    for item in items:
        if 'password' in item:
            del item['password']
    return items


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
                await transaction.execute_query(Query.update(user)
                                                .set(user.time_updated, time_updated)
                                                .where(user.name == name)
                                                .get_sql())
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
    async def get_setids(self, prefixes, discarded=False, dbids=False, transaction=None):
        setids = set()
        for prefix in prefixes:
            if isinstance(prefix, SetID):
                prefix = str(prefix)
            setid = await Dataset.filter(setid__startswith=prefix, discarded=discarded)\
                                 .limit(2)\
                                 .using_db(transaction)\
                                 .values_list('id' if dbids else 'setid', flat=True)
            if not setid:
                discarded = 'discarded ' if discarded else ''
                raise NoSetidFound(f'{prefix} does not match any {discarded}dataset')
            if len(setid) > 1:
                matches = '\n  '.join([f'{x}' for x in setid])
                raise MultipleSetidFound(f'{prefix} matches multiple:\n'
                                         f'  {matches}\n'
                                         f'Use "{prefix}*" to mean all these.')
            setids.add(setid[0])
        return sorted(setids)

    @run_in_transaction
    async def get_datasets_by_setids(self, setids, prefetch, transaction=None):
        ids = await self.get_setids(setids, dbids=True, transaction=transaction)
        query = Dataset.filter(id__in=ids).using_db(transaction)
        if prefetch:
            query = query.prefetch_related(*prefetch)
        return await query

    @run_in_transaction
    async def get_datasets_by_dbids(self, ids, prefetch, transaction=None):
        query = Dataset.filter(id__in=ids).using_db(transaction)
        if prefetch:
            query = query.prefetch_related(*prefetch)
        return await query

    @run_in_transaction
    async def get_filepath_by_setid_idx(self, setid, idx, transaction=None):
        if isinstance(setid, SetID):
            setid = str(setid)
        file = await File.get(dataset__setid=setid, idx=idx).using_db(transaction)
        return file.path

    @run_in_transaction
    async def get_all_known_for_collection(self, collection, transaction=None):
        descs = [x for x in collection.table_descriptors if x.through]
        all_known = {
            desc.key: [
                x['value'] for x in await transaction.execute_query(Query.from_(desc.table)
                                                                    .select('value')
                                                                    .get_sql())
            ]
            for desc in descs
            if {'any', 'all'}.intersection(collection.filter_specs[desc.key].operators)
        }
        all_known.update({
            'status': list(STATUS),
            'tags': (await (Tag.filter(collection=collection.name)
                            .using_db(transaction)
                            .order_by('value')
                            .values_list('value', flat=True))),
        })
        return all_known

    @run_in_transaction   # noqa: C901
    async def get_filtered_listing(self, descs, filters, transaction=None):
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        listing, dataset, dataset_tag, tag = \
            Tables(descs[0].table, 'dataset', 'dataset_tag', 'tag')  # pylint: disable=unbalanced-tuple-unpacking

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
                     .where(dataset.discarded != True)  # pylint: disable=singleton-comparison

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
        return await transaction.execute_query(query.get_sql())

    @run_in_transaction
    async def get_datasets_for_collections(self, collections, transaction=None):
        query = Dataset.filter(discarded__not=True).using_db(transaction)
        if collections is not None:
            query = query.filter(collection__in=collections)
        return [SetID(x['setid'])
                for x in await query.values('setid', 'status')
                if not x['status'] & STATUS_MISSING]

    @run_in_transaction
    async def get_all_known_tags_for_collection(self, collection, transaction=None):
        return await Tag.filter(collection=collection)\
                        .using_db(transaction)\
                        .order_by('value')\
                        .values_list('value', flat=True)

    @run_in_transaction
    async def delete_comments_tags(self, setids, comments, tags, transaction=None):
        ids = await self.get_setids(setids, dbids=True, transaction=transaction)
        if tags:
            dataset_tag = Table('dataset_tag')
            await transaction.execute_query(Query.from_(dataset_tag)
                                            .where(dataset_tag.dataset_id.isin(ids))
                                            .delete()
                                            .get_sql())

        if comments:
            await Comment.filter(dataset_id__in=ids).using_db(transaction).delete()

    @run_in_transaction
    async def discard_datasets(self, setids, transaction=None):
        ids = await self.get_setids(setids, dbids=True, transaction=transaction)
        await Dataset.filter(id__in=ids).using_db(transaction)\
                     .update(discarded=True)

    @run_in_transaction
    async def discard_datasets_by_dbid(self, ids, transaction=None):
        await Dataset.filter(id__in=ids).using_db(transaction)\
                     .update(discarded=True)

    @run_in_transaction
    async def undiscard_datasets(self, setids, transaction=None):
        ids = await self.get_setids(setids, dbids=True, discarded=True, transaction=transaction)
        await Dataset.filter(id__in=ids).using_db(transaction)\
                     .update(discarded=False)

    @run_in_transaction
    async def update_tags_for_setids(self, setids, add, remove, transaction=None):
        setids = [str(x) for x in await self.get_setids(setids, transaction=transaction)]
        dataset = Table('dataset')
        colids = await transaction.execute_query(Query.from_(dataset)
                                                 .where(dataset.setid.isin(setids))
                                                 .select(dataset.collection, dataset.id)
                                                 .get_sql())
        add = [
            (colid['collection'], tag, colid['id'])
            for tag, colid in product(add, colids)
        ]
        remove = [
            (colid['collection'], tag, colid['id'])
            for tag, colid in product(remove, colids)
        ]
        await self.bulk_tag(add, remove, transaction=transaction)

    @run_in_transaction
    async def comment_multiple(self, setids, user, message, transaction=None):
        ids = await self.get_setids(setids, dbids=True, transaction=transaction)
        await User.get(name=user).using_db(transaction)
        now = int(utils.now() * 1000)
        comments = [
            Comment(dataset_id=id, author=user, time_added=now, text=message)
            for id in ids
        ]
        await Comment.bulk_create(comments, using_db=transaction)

    @run_in_transaction
    async def bulk_comment(self, comments, transaction=None):
        await Comment.bulk_create([Comment(**dct) for dct in comments], using_db=transaction)

    @run_in_transaction
    async def bulk_tag(self, add, remove, transaction=None):
        tag, dataset_tag, tmp = Tables('tag', 'dataset_tag', 'tmp')  # pylint: disable=unbalanced-tuple-unpacking
        names = [x for x, y in groupby(add, key=lambda k: (k[0], k[1]))]
        if add:
            need = Query().from_(Tuple(*names))\
                          .select('*')\
                          .get_sql()\
                          .replace('((', '(VALUES(', 1)
            have = Query().from_(tag)\
                          .select(tag.collection, tag.value)\
                          .get_sql()
            insert = f'INSERT INTO tag (collection, value) SELECT * FROM ({need} EXCEPT {have})'
            await transaction.execute_query(insert)

            need = Query.with_(Query.with_(Query.from_(Tuple(*add))
                                           .select('*'), 'tmp(collection, value, dataset_id)')
                               .from_(tmp)
                               .join(tag)
                               .on((tmp.collection == tag.collection) & (tmp.value == tag.value))
                               .select(tag.id, tmp.dataset_id), 'x(tag_id, dataset_id)')\
                        .from_('x')\
                        .select(tmp.tag_id, tmp.dataset_id)\
                        .get_sql()\
                        .replace('((', '(VALUES(', 1)
            have = Query.from_(dataset_tag)\
                        .select(dataset_tag.tag_id, dataset_tag.dataset_id)\
                        .get_sql()
            insert_rel = \
                f'INSERT INTO dataset_tag (tag_id, dataset_id) SELECT * FROM ({need}) EXCEPT {have}'
            await transaction.execute_query(insert_rel)

        if remove:
            kill = Query.with_(Query.with_(Query.from_(Tuple(*remove))
                                           .select('*'), 'tmp(collection, value, dataset_id)')
                               .from_(tmp)
                               .join(tag)
                               .on((tmp.collection == tag.collection) & (tmp.value == tag.value))
                               .join(dataset_tag)
                               .on((tag.id == dataset_tag.tag_id)
                                   & (tmp.dataset_id == dataset_tag.dataset_id))
                               .select(tag.id, tmp.dataset_id), 'x(tag_id, dataset_id)')\
                        .from_('x')\
                        .select(tmp.tag_id, tmp.dataset_id)
            await transaction.execute_query(Query.from_(dataset_tag)
                                            .delete()
                                            .select(dataset_tag.tag_id, dataset_tag.dataset_id)
                                            .where(Tuple(dataset_tag.tag_id, dataset_tag.dataset_id)
                                                   .isin(kill))
                                            .get_sql()
                                            .replace('((', '(VALUES('))

    @run_in_transaction
    async def get_comments_for_setids(self, setids, transaction=None):
        ids = await self.get_setids(setids, dbids=True, transaction=transaction)
        filters = {}
        if ids:
            filters['dataset_id__in'] = ids
        else:
            filters['dataset__discarded__not'] = 1
        return await Comment.filter(**filters).using_db(transaction).prefetch_related('dataset')

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
    async def delete_comments_by_ids(self, ids, transaction=None):
        await Comment.filter(id__in=ids).using_db(transaction).delete()

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
    async def list_tags(self, collections=None, transaction=None):
        return await ((Tag.filter(collection__in=collections) if collections else Tag.all())
                      .using_db(transaction)
                      .distinct()
                      .order_by('value')
                      .values_list('value', flat=True))

    @run_in_transaction
    async def cleanup_tags(self, transaction=None):
        tag, dataset_tag = Tables('tag', 'dataset_tag')  # pylint: disable=unbalanced-tuple-unpacking
        await transaction.execute_query(Query.from_(tag)
                                        .where(tag.id.notin(Query.from_(dataset_tag)
                                                            .select(dataset_tag.tag_id)))
                                        .delete()
                                        .get_sql())

    @run_in_transaction
    async def cleanup_listing_relations(self, descs, transaction=None):
        for desc in [y for x in descs.values() for y in x if y.through]:
            rel = Table(desc.table)
            await transaction.execute_query(Query.from_(rel)
                                            .where(rel.id.notin(Query.from_(desc.through)
                                                                .select(desc.rel_id)
                                                                .distinct()))
                                            .delete()
                                            .get_sql())

    @run_in_transaction
    async def cleanup_discarded(self, descs, transaction=None):
        datasets = await Dataset.filter(discarded=True)\
                                .using_db(transaction)\
                                .order_by('collection')\
                                .values_list('collection', 'id')
        if not datasets:
            return

        datasets = [
            (col, [x[1] for x in tuples])
            for col, tuples in groupby(datasets, lambda x: x[0])
        ]
        for col, ids in datasets:
            dataset = Table('dataset')
            await transaction.execute_query(Query.from_(dataset)
                                            .where(dataset.id.isin(ids))
                                            .delete()
                                            .get_sql())

            for table in (Table('dataset_tag'), Table('comment'), Table('file')):
                await transaction.execute_query(Query.from_(table)
                                                .where(table.dataset_id.isin(ids))
                                                .delete()
                                                .get_sql())

            tbls = descs[col]
            assert not tbls[0].through, 'Listing table should be first'
            listing = Table(tbls[0].table)

            await transaction.execute_query(Query.from_(listing)
                                            .where(listing.id.isin(ids))
                                            .delete()
                                            .get_sql())

            for desc in [x for x in tbls if x.through]:
                through = Table(desc.through)
                id_field = getattr(through, desc.listing_id)
                await transaction.execute_query(Query.from_(through)
                                                .where(id_field.isin(ids))
                                                .delete()
                                                .get_sql())

    @run_in_transaction
    async def query(self, collections=None, discarded=None, outdated=None, path=None, tags=None,
                    abbrev=None, missing=None, transaction=None):
        # pylint: disable=too-many-arguments, too-many-locals

        abbrev = 10 if abbrev is True else abbrev
        discarded = bool(discarded)

        dataset = Table('dataset')
        query = Query.from_(dataset)

        if collections:
            query = query.where(dataset.collection.isin(collections))

        if outdated:
            status_ids = list(STATUS.keys())
            bitmask = 2**status_ids.index(STATUS_OUTDATED)
            query = query.where(dataset.status.bitwiseand(bitmask) == bitmask)

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
                     .orderby(dataset.setid)\
                     .get_sql()

        datasets = await transaction.execute_query(query)
        return [
            x['setid'][:abbrev] if abbrev else x['setid']
            for x in datasets
        ]

    @run_in_transaction
    async def ensure_values(self, tablename, values, transaction=None):
        table = Table(tablename)
        need = Query().from_(Tuple(*values))\
                      .select('*')\
                      .get_sql()\
                      .replace('((', '(VALUES(', 1)
        have = Query().from_(table)\
                      .select(table.value)\
                      .get_sql()
        await transaction.execute_query(
            f'INSERT INTO {table} (value) SELECT * FROM ({need} EXCEPT {have})')

    @run_in_transaction
    async def ensure_relations(self, relname, throughname, rel_id, back_id, relations,
                               transaction=None):
        # pylint: disable=too-many-arguments, too-many-locals
        rel = Table(relname)
        through = Table(throughname)
        tmp = Table('tmp')
        relid = getattr(through, rel_id)
        backid = getattr(through, back_id)
        needq = Query.with_(Query.with_(Query.from_(Tuple(*relations))
                                        .select('*'), 'tmp(value, back_id)')
                            .from_(tmp)
                            .join(rel)
                            .on(tmp.value == rel.value)
                            .select(rel.id, tmp.back_id), 'ins(rel_id, back_id)')\
                     .from_('ins')\
                     .select(tmp.rel_id, tmp.back_id)

        need = needq.get_sql().replace('((', '(VALUES(', 1)
        have = Query.from_(through)\
                    .select(relid, backid)\
                    .get_sql()
        await transaction.execute_query(
            f'INSERT INTO {through} ({rel_id}, {back_id}) SELECT * FROM ({need}) EXCEPT {have}')
        await transaction.execute_query(Query.from_(through)
                                        .where(backid.isin({x[1] for x in relations})
                                               & ~Tuple(relid, backid).isin(needq))
                                        .delete()
                                        .get_sql()
                                        .replace('((', '(VALUES(', 1))

    @run_in_transaction  # noqa: C901
    async def rpc_query(self, model, filters, attrs, order, limit, offset, transaction=None):
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

        qres = await transaction.execute_query(query.get_sql())
        result.setdefault(model, []).extend(cleanup_attrs(qres))

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
                tablename = field.type._meta.table
                subtable = Table(tablename)
                if '*' not in select and field.relation_field not in select:
                    select.append(field.relation_field)
                query = Query.from_(subtable)\
                             .select(*select)\
                             .where(getattr(subtable, field.relation_field).isin(ids))\
                             .get_sql()
                relres = await transaction.execute_query(query)
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
                tablename = field.type._meta.table
                rel = Table(tablename)
                query = Query.from_(through)\
                             .select(field.backward_key, field.forward_key)\
                             .where(getattr(through, field.backward_key).isin(ids))\
                             .get_sql()
                links = await transaction.execute_query(query)
                for prime in qres:
                    prime[fieldname] = [
                        x[field.forward_key]
                        for x in links
                        if x[field.backward_key] == prime['id']
                    ]
                query = Query.from_(rel)\
                             .select(*select)\
                             .where(rel.id.isin({x[field.forward_key] for x in links}))\
                             .get_sql()
                relres = await transaction.execute_query(query)
                result.setdefault(tablename, []).extend(cleanup_attrs(relres))

            else:
                raise ValueError(f'field {fieldname} not on model {model}')

        return result


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
            conn = connection._in_transaction()  # pylint: disable=protected-access
            await conn.start()
            return conn

    conn = await T2.transaction()

    master = Table('sqlite_master')
    tables = {
        x['name']: Table(x['name'])
        for x in await conn.execute_query(Query.from_(master)
                                          .select(master.name)
                                          .where((master.type == 'table')
                                                 & master.name.not_like('sqlite_%')
                                                 & master.name.not_like('l_%'))
                                          .get_sql())
    }

    comments = {}
    comment_t = tables.pop('comment')
    items = await conn.execute_query(Query.from_(comment_t)
                                     .select(comment_t.star)
                                     .orderby(comment_t.dataset_id)
                                     .orderby(comment_t.id)
                                     .get_sql())
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
    items = await conn.execute_query(Query.from_(file_t)
                                     .select(file_t.star)
                                     .orderby(file_t.dataset_id)
                                     .orderby(file_t.id)
                                     .get_sql())
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
    items = await conn.execute_query(Query.from_(dataset_tag_t)
                                     .join(tag_t)
                                     .on(dataset_tag_t.tag_id == tag_t.id)
                                     .select('*')
                                     .orderby(dataset_tag_t.dataset_id)
                                     .orderby(tag_t.value)
                                     .get_sql())

    for did, grp in groupby(items, key=lambda x: x['dataset_id']):
        assert did not in tags
        tags[did] = lst = []
        for tag in grp:
            del tag['dataset_id']
            del tag['collection']
            del tag['id']
            del tag['tag_id']
            lst.append(tag.pop('value'))
            assert not tag

    dump = {}
    dump['datasets'] = collections = {}
    dataset_t = tables.pop('dataset')
    items = await conn.execute_query(Query.from_(dataset_t)
                                     .select('*')
                                     .orderby(dataset_t.setid)
                                     .get_sql())
    for dataset in items:
        did = dataset.pop('id')  # Everything except this is included in the dump
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
    items = await conn.execute_query(Query.from_(user_group_t)
                                     .join(group_t)
                                     .on(user_group_t.group_id == group_t.id)
                                     .select('*')
                                     .orderby(user_group_t.user_id)
                                     .orderby(group_t.name)
                                     .get_sql())
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
    items = await conn.execute_query(Query.from_(user_t)
                                     .select('*')
                                     .orderby(user_t.name)
                                     .get_sql())
    for user in items:
        user_id = user.pop('id')  # Everything except this is included in the dump
        user['groups'] = groups.pop(user_id, [])
        user['time_created'] = int((datetime.fromisoformat(user['time_created'])
                                    - datetime.fromtimestamp(0)).total_seconds())  # noqa: DTZ
        user['time_updated'] = int((datetime.fromisoformat(user['time_updated'])
                                    - datetime.fromtimestamp(0)).total_seconds())  # noqa: DTZ
        users.append(user)

    assert not groups, groups
    assert not tables, tables.keys()

    await conn.commit()
    await T2.close_connections()
    return dump
