# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest


async def test_user(site):
    # pylint: disable=too-many-statements

    assert not await site.db.authenticate('', '')
    assert not await site.db.authenticate('marv', 'test')

    await site.db.user_add('marv', 'test', 'marv', '')

    with pytest.raises(ValueError):
        await site.db.user_add('marv', 'test', 'marv', '')

    await site.db.user_add('admin', 'admin_pw', 'marv', '',
                           given_name='John', family_name='Doe',
                           email='john@doe.com',
                           time_created=10, time_updated=10)

    await site.db.user_add('admin2',
                           '$2b$12$3LFRuJWVGMsOyaOHAVNOUu0IRM/VCehCuOiRRA/7qc4ZlxUo.NcuS',
                           'marv', '',
                           given_name='John', family_name='Doe',
                           email='john@doe.com',
                           time_created=10, time_updated=10, _restore=True)

    assert await site.db.authenticate('marv', 'test')
    assert not await site.db.authenticate('marv', 'wrong pw')
    assert await site.db.authenticate('admin', 'admin_pw')
    assert await site.db.authenticate('admin2', 'admin')

    await site.db.user_pw('marv', 'test2')
    assert await site.db.authenticate('marv', 'test2')

    with pytest.raises(ValueError):
        await site.db.user_pw('not a user', 'test2')

    await site.db.user_rm('admin2')
    assert not await site.db.authenticate('admin2', 'admin')
    with pytest.raises(ValueError):
        await site.db.user_rm('admin2')

    await site.db.group_add('management')
    with pytest.raises(ValueError):
        await site.db.group_add('management')

    with pytest.raises(ValueError):
        await site.db.group_adduser('no group', 'marv')

    with pytest.raises(ValueError):
        await site.db.group_adduser('management', 'no user')

    await site.db.group_adduser('management', 'marv')
    await site.db.group_adduser('management', 'marv')

    await site.db.group_rmuser('management', 'marv')

    with pytest.raises(ValueError):
        await site.db.group_rmuser('no group', 'marv')

    with pytest.raises(ValueError):
        await site.db.group_rmuser('management', 'no user')

    await site.db.group_rm('management')
    with pytest.raises(ValueError):
        await site.db.group_rm('management')

    await site.db.group_add('finance')
    await site.db.group_add('qa')
    await site.db.group_adduser('qa', 'admin')
    await site.db.group_adduser('qa', 'marv')

    await site.db.bulk_um(
        users_add=['foo', 'bar'],
        users_remove=['marv'],
        groups_add=['manage'],
        groups_remove=['finance'],
        groups_add_users=[('qa', ('foo',)), ('manage', ('foo', 'admin'))],
        groups_remove_users=[('qa', ('admin',))],
    )

    res = [x.name for x in await site.db.get_users()]
    assert res == ['adm', 'admin', 'bar', 'foo', 'test']

    res = [[y.name for y in x.groups] for x in await site.db.get_users(deep=True)]
    assert res == [['admin'], ['manage'], [], ['qa', 'manage'], []]

    res = [x.name for x in await site.db.get_groups()]
    assert res == ['admin', 'manage', 'qa']

    res = [[y.name for y in x.users] for x in await site.db.get_groups(deep=True)]
    assert res == [['adm'], ['admin', 'foo'], ['foo']]

    res = await site.db.get_user_by_name('admin')
    assert res.name == 'admin'

    res = await site.db.get_user_by_name('admin', deep=True)
    assert res.name == 'admin'
    assert [x.name for x in res.groups] == ['manage']

    res = await site.db.get_user_by_realmuid('marv', '', deep=True)
    assert res.name == 'test'
    assert not list(res.groups)

    res = await site.db.get_user_by_realmuid('not an uid', '')
    assert not res
