# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from collections import OrderedDict, namedtuple
from contextlib import contextmanager

from sqlalchemy import Boolean, Column, Float, ForeignKey, Index, Integer, String, Table
from sqlalchemy import event, schema
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from marv_node.setid import SetID
from .utils import underscore_to_camelCase

_LISTING_PREFIX = ''  # Only for testing

STATUS = OrderedDict((
    ('error', 'ERROR: One or more errors occured while processing this dataset'),
    ('missing', 'MISSING: One or more files of this dataset are missing'),
    ('outdated', 'OUTDATED: There are outdated nodes for this dataset'),
    ('pending', 'PENDING: There are pending node runs'),
))
STATUS_ERROR = 1
STATUS_MISSING = 2
STATUS_OUTDATED = 4
STATUS_PENDING = 8


Model = declarative_base(name='Model')


@contextmanager
def scoped_session(site):
    """Transaction scope for database operations."""
    session = site.session()
    try:
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


@event.listens_for(Engine, 'connect')
def set_sqlite_pragma_connect(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    # page_size must be before journal_mode
    cursor.execute('PRAGMA foreign_keys=ON;')
    cursor.execute('PRAGMA page_size=4096;')
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA synchronous=NORMAL;')
    # TODO: we don't want the websever to checkpoint,
    # ever. Checkpointing should happen via cli.
    cursor.close()


@event.listens_for(Engine, 'close')
def set_sqlite_pragma_close(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA optimize;')  # ignored prior to 3.18.0
    cursor.close()


@compiles(schema.CreateTable)
def compile(element, compiler, **kw):
    text = compiler.visit_create_table(element, **kw)
    if element.element.info.get('without_rowid'):
        text = text.rstrip() + ' WITHOUT ROWID\n\n'
    return text


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


dataset_tag = Table(  # pylint: disable=invalid-name
    'dataset_tag',
    Model.metadata,
    Column('dataset_id', Integer, ForeignKey('dataset.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True),
    info={'without_rowid': True},
)


class Dataset(Model):
    __tablename__ = 'dataset'
    id = Column(Integer, primary_key=True)

    # TODO: consider Collection model
    collection = Column(String)
    discarded = Column(Boolean, default=False)
    name = Column(String)
    status = Column(Integer, default=0)
    time_added = Column(Integer, nullable=False)  # ms since epoch
    timestamp = Column(Integer, nullable=False)  # ms since epoch

    _setid = Column('setid', String, unique=True, nullable=False)
    @hybrid_property
    def setid(self):
        return SetID(self._setid)

    @setid.setter
    def setid(self, value):
        self._setid = str(value)

    @setid.expression
    def setid(self):
        return self._setid

    comments = relationship('Comment', back_populates='dataset', lazy='raise')
    files = relationship('File', back_populates='dataset', lazy='joined')
    # Handled via backref on Tag
    # tags = relationship('Tag', secondary=dataset_tag, lazy='raise',
    #                        back_populates='datasets'),

    error = make_status_property(1)
    missing = make_status_property(2)
    outdated = make_status_property(4)
    pending = make_status_property(8)

    def __repr__(self):
        return f'<{type(self).__name__} {self.setid} {self.name}>'


class File(Model):
    # pylint: disable=too-few-public-methods

    __tablename__ = 'file'
    __table_args__ = (
        {'info': {'without_rowid': True}},
    )
    dataset_id = Column(Integer, ForeignKey('dataset.id'), primary_key=True)
    idx = Column(Integer, primary_key=True)  # files are counted per dataset

    missing = Column(Boolean, default=False)
    mtime = Column(Integer, nullable=False)  # ms since epoch
    path = Column(String, nullable=False)
    size = Column(Integer, nullable=False)

    dataset = relationship('Dataset', back_populates='files', lazy='raise')

    def __repr__(self):
        return f"<{type(self).__name__} '{self.path}'>"


class Comment(Model):
    # pylint: disable=too-few-public-methods

    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('dataset.id'))

    author = Column(String, nullable=False)
    time_added = Column(Integer, nullable=False)  # ms since epoch
    text = Column(String, nullable=False)

    dataset = relationship('Dataset', back_populates='comments', lazy='raise')


class Tag(Model):
    # pylint: disable=too-few-public-methods

    __tablename__ = 'tag'
    __table_args__ = (
        Index('idx_tag_collection_value', 'collection', 'value', unique=True),
    )
    id = Column(Integer, primary_key=True)
    collection = Column(String, nullable=False)
    value = Column(String)
    datasets = relationship('Dataset', secondary=dataset_tag, lazy='raise',
                            backref='tags')


user_group = Table(  # pylint: disable=invalid-name
    'user_group',
    Model.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('group.id'), primary_key=True),
    info={'without_rowid': True},
)


class User(Model):
    # pylint: disable=too-few-public-methods

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    password = Column(String)
    given_name = Column(String)
    family_name = Column(String)
    email = Column(String)
    realm = Column(String, nullable=False)
    realmuid = Column(String)
    time_created = Column(Integer, nullable=False)
    time_updated = Column(Integer, nullable=False)


class Group(Model):
    # pylint: disable=too-few-public-methods

    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    # TODO: switch to lazy raise
    users = relationship('User', secondary=user_group, backref='groups')


# pylint: disable=invalid-name
dataset = Dataset.__table__
file = File.__table__
comment = Comment.__table__
tag = Tag.__table__
user = User.__table__
group = Group.__table__
# pylint: enable=invalid-name

ListingModel = namedtuple('ListingModel', 'Listing relations secondaries')


def make_listing_model(name, filter_specs):
    relations = {}
    secondaries = {}
    listing_name = f'{_LISTING_PREFIX}listing_{name}'
    listing_model_name = underscore_to_camelCase(listing_name)
    listingid = f'{listing_name}.id'

    def generate_relation(fname):
        sec_name = f'{listing_name}_{fname}_sec'
        rel_name = f'{listing_name}_{fname}'
        rel_model_name = underscore_to_camelCase(rel_name)
        relid = f'{rel_name}.id'
        assert '_' not in rel_model_name, rel_model_name
        secondary = Table(
            sec_name,
            Model.metadata,
            Column('listing_id', Integer, ForeignKey(listingid), primary_key=True),
            Column('relation_id', Integer, ForeignKey(relid), primary_key=True),
            info={'without_rowid': True},
        )
        secondaries[fname] = secondary
        relations[fname] = type(rel_model_name, (Model,), {
            '__tablename__': rel_name,
            'id': Column(Integer, primary_key=True),
            'value': Column(String, index=True, unique=True),
            'listing': relationship(listing_model_name,
                                    secondary=secondary,
                                    lazy='raise',
                                    back_populates=fname),
            '__repr__': lambda self: f'<{type(self).__name__} {self.id} {self.value!r}>',
        })
        return relationship(rel_model_name, secondary=secondary,
                            lazy='raise', back_populates='listing')

    coltype_factories = {
        # All dates and times in ms (since epoch)
        'datetime': lambda name: Column(Integer),
        'filesize': lambda name: Column(Integer),
        'float': lambda name: Column(Float),
        'int': lambda name: Column(Integer),
        'string': lambda name: Column(String),
        'string[]': generate_relation,
        'subset': generate_relation,
        'timedelta': lambda name: Column(Integer),
        'words': lambda name: Column(String),
    }

    dct = {
        '__tablename__': listing_name,
        '__table_args__': (
            {'info': {'without_rowid': True}}
        ),
        'id': Column(Integer, ForeignKey('dataset.id'), primary_key=True),
        'row': Column(String),
        'dataset': relationship('Dataset'),
        '__repr__': lambda self: f'<{type(self).__name__} {self.id}>',
    }
    assert not filter_specs.keys() & dct.keys()
    dct.update((fspec.name, coltype_factories[fspec.value_type](fspec.name))
               for fspec in filter_specs.values()
               if fspec.name not in ('comments', 'status', 'tags'))

    Listing = type(listing_model_name, (Model,), dct)
    return ListingModel(Listing, relations, secondaries)
