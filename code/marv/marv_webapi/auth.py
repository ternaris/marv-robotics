# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import time

import bcrypt
import flask
import jwt
from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from marv import utils
from marv.model import Group, User, db
from .tooling import api_group as marv_api_group


# TODO: switch to idempotent OR IGNORE (like tag.py)
# TODO: move (part) of this to site
class UserManager:
    @staticmethod
    def authenticate(username, password):
        if not username or not password:
            return False
        try:
            user = db.session.query(User).filter_by(name=username, realm='marv').one()
        except NoResultFound:
            return False
        hashed = user.password.encode('utf-8')
        return bcrypt.hashpw(password, hashed) == hashed

    @staticmethod
    def user_add(name, password, realm, realmuid, given_name=None, family_name=None,
                 email=None, time_created=None, time_updated=None, _restore=None):
        # pylint: disable=too-many-arguments
        try:
            if not _restore:
                password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            now = int(utils.now())
            if not time_created:
                time_created = now
            if not time_updated:
                time_updated = now
            user = User(name=name, password=password, realm=realm, given_name=given_name,
                        family_name=family_name, email=email, realmuid=realmuid,
                        time_created=time_created, time_updated=time_updated)
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            raise ValueError(f'User {name} exists already')

    @staticmethod
    def user_rm(username):
        try:
            user = db.session.query(User).filter_by(name=username).one()
            db.session.delete(user)
            db.session.commit()
        except NoResultFound:
            raise ValueError(f'User {username} does not exist')

    @staticmethod
    def user_pw(username, password):
        try:
            user = db.session.query(User).filter_by(name=username).one()
        except NoResultFound:
            raise ValueError(f'User {username} does not exist')

        user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user.time_updated = int(utils.now())
        db.session.commit()

    @staticmethod
    def group_add(groupname):
        try:
            group = Group(name=groupname)
            db.session.add(group)
            db.session.commit()
        except IntegrityError:
            raise ValueError(f'Group {groupname} exists already')

    @staticmethod
    def group_rm(groupname):
        try:
            group = db.session.query(Group).filter_by(name=groupname).one()
            db.session.delete(group)
            db.session.commit()
        except NoResultFound:
            raise ValueError(f'Group {groupname} does not exist')

    @staticmethod
    def group_adduser(groupname, username):
        try:
            group = db.session.query(Group).filter_by(name=groupname).one()
        except NoResultFound:
            raise ValueError(f'Group {groupname} does not exist')
        try:
            user = db.session.query(User).filter_by(name=username).one()
        except NoResultFound:
            raise ValueError(f'User {username} does not exist')
        group.users.append(user)
        db.session.commit()

    @staticmethod
    def group_rmuser(groupname, username):
        try:
            group = db.session.query(Group).filter_by(name=groupname).one()
        except NoResultFound:
            raise ValueError(f'Group {groupname} does not exist')
        try:
            user = db.session.query(User).filter_by(name=username).one()
        except NoResultFound:
            raise ValueError(f'User {username} does not exist')
        if user in group.users:
            group.users.remove(user)
        db.session.commit()

    @staticmethod
    def check_authorization(acl, authorization):
        username = None
        groups = {'__unauthenticated__'}
        if authorization:
            try:
                token = authorization.replace('Bearer ', '')
                session = jwt.decode(token, current_app.config['SECRET_KEY'])
                user = db.session.query(User).filter_by(name=session['sub']).one()
            except Exception:  # pylint: disable=broad-except
                flask.abort(401)
            if user.time_updated > session['iat']:
                flask.abort(401)
            username = user.name
            groups = {g.name for g in user.groups}
            groups.add('__authenticated__')

        elif '__unauthenticated__' not in acl:
            flask.abort(401)

        if acl and not acl.intersection(groups):
            flask.abort(403)

        flask.request.username = username
        flask.request.user_groups = groups


@marv_api_group()
def auth(app):
    assert not hasattr(app, 'um')  # TODO: correct place for extension
    app.um = UserManager()


def generate_token(username):
    now = int(time.time())
    return jwt.encode({
        'exp': now + 2419200,  # 4 weeks expiration
        'iat': now,
        'sub': username,
    }, current_app.config['SECRET_KEY'])


@auth.endpoint('/auth', methods=['POST'], force_acl=['__unauthenticated__'])
def auth_post():
    req = flask.request.get_json()
    if not req:
        flask.abort(400)
    username = req.get('username', '')
    password = req.get('password', '').encode('utf-8')

    if not current_app.um.authenticate(username, password):
        return flask.abort(422)

    return flask.jsonify({'access_token': generate_token(username).decode('utf-8')})
