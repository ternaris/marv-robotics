.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _migrate:

Migration
=========

Listed here are all versions that necessitate migration. Depending on the version you are migrating from you might need to follow multiple migration steps.

In case of database migrations it is sufficient to ``marv dump`` the database with the version you are currently using and ``marv restore`` with the latest version; marv is able to *dump* itself and *restore* any older version. In case this does not hold true ``marv restore`` will complain and provide instructions what to do.

.. _migrate-20.04.0:

20.04.0
-------

Database migration
^^^^^^^^^^^^^^^^^^
An updated version of tortoise-orm required changes to the database schemas. A migration of the MARV database is necessary. Export the database with your current version of MARV:

.. code-block:: console

   marv dump dump-1911.json
   mv db/db.sqlite db/db.sqlite.1911

After updating MARV run:

.. code-block:: console

   marv init
   marv restore dump-1911.json


.. _migrate-19.11.0:

19.11.0
-------

The gunicorn configuration was simplified. Instead of providing ``gunicorn_cfg.py`` and running gunicorn manually, the ``marv serve`` cli was added. Check it out with ``marv serve --help``.

If you were overriding the dburi path in your marv.conf, there is no need for the odd sqlalchemy URIs with four slashes anymore. If your custom dburi starts with ``sqlite:////`` please remove one slash.

This version makes the switch from sqlalchemy to tortoise as the underlying ORM, which makes a migration of the MARV database necessary. Export the database with your current version of MARV:

.. code-block:: console

   marv dump dump-1909.json
   mv db/db.sqlite db/db.sqlite.1909

After updating MARV run:

.. code-block:: console

   marv init
   marv restore dump-1909.json


.. _migrate-19.09.0:

19.09.0
-------

Uwsgi was replaced in favour of Gunicorn. In your site directory, replace ``uwsgi.conf`` with a ``gunicorn_cfg.py``:

.. code-block:: python

   """Gunicorn configuration for MARV."""

   import multiprocessing
   import pathlib

   # pylint: disable=invalid-name

   bind = ':8000'
   proc_name = 'marvweb'
   raw_env = {
       f'MARV_CONFIG={pathlib.Path(__file__).parent.resolve() / "marv.conf"}',
   }
   workers = multiprocessing.cpu_count() * 2 + 1
   worker_class = 'aiohttp.GunicornUVLoopWebWorker'

If you made any changes to your old ``uwsgi.conf`` please adjust the above config accordingly. If you are using an nginx reverse proxy you also have to adjust its configuration. Replace any ``uwsgi_pass`` directives with a ``proxy_pass``:

.. code-block:: diff

   -       uwsgi_pass 127.0.0.1:8000;
   -       include uwsgi_params;
   +       proxy_set_header Host $host;
   +       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   +       proxy_pass 127.0.0.1:8000;


.. _migrate-19.02.0:

19.02.0
-------

Support for ipdb has been dropped in favour of `pdb++ <https://github.com/antocuni/pdb>`_. Use ``PDB=1 marv run`` instead of ``marv-ipdb run``. For more information see :ref:`debug`.


.. _migrate-18.07:

18.07
-----

The way inputs are handled has changed. Inputs selecting an individual topic are now optional. See :ref:`optional_inputs` for more information.


.. _migrate-18.04:

18.04
-----

The list of system dependencies is updated and the installation has significantly changed. We recommend that you re-read the :ref:`install` instructions. The database has not changed and existing sites continue to function without migration.

MARV now supports offloading the delivery of files to nginx. In case you are not using nginx as reverse-proxy, yet, you should seriously consider to change that now. See :ref:`cfg_marv_reverse_proxy` and :ref:`deploy_nginx`.

MARV now supports access control lists (ACLs). The default ACL requires authentication to read anything, tag and comment; and only members of the group admin may discard datasets. For users of the Enterprise Edition this corresponds to the same behaviour as before. The :func:`marv_webapi.acls.public` closely resembles the previous Community Edition default, apart from requiring admin group membership to discard datasets. See :ref:`cfg_marv_acl` to change the effective ACL.


.. _migrate-18.03:

18.03
-----

With this release:

- geojson property object has changed.

To update the store to the new format rerun the trajectory nodes using:

.. code-block:: console

   marv run --node trajectory --force --force-dependent --collection=*


.. _migrate-18.02:

18.02
-----

With this release:

- message definitions are read from bag files instead of being expected on the system
- marv allows mixing message types per topic.

As part of this the topics section has been renamed to ``connections_section`` and the ``bagmeta`` node has changed a bit. Please update your configuration along the lines of:

.. literalinclude:: 1711-1802-marv.conf.diff
   :language: diff

And then rerun the bagmeta node and the new connections section.

.. code-block:: console

   marv run --node bagmeta --node connections_section --force --collection=*

Now, nodes can be run, that were previously missing message type definitions. ``gnss_plots`` for example works differently, if it cannot find navsat orientations. To rerun it and all nodes depending on it:

.. code-block:: console

   marv run --node gnss_plots --force --force-dependent --collection=*


.. _migrate-17.11:

17.11
-----

In the old site:

1. **Make sure you have a backup of your old site!**

2. Dump database of old marv:

   .. code-block:: console

      curl -LO https://gist.githubusercontent.com/chaoflow/02a1be706cf4948a9f4d7f1fd66d6c73/raw/de4feab88bcfa756abfb6c7f5a8ccaef7f25b36d/marv-16.10-dump.py
      python2 marv-16.10-dump.py > /tmp/dump.json

For and in the new instance:

3. Follow :ref:`install` and :ref:`setup-basic-site` to setup a basic site.

4. Replace ``marv.conf`` with the default :ref:`config` and adjust as needed (e.g. scanroot).

5. Initialize site with new configuration:

   .. code-block:: console

      marv init

6. If your scanroot has moved, adjust paths as needed:

   .. code-block:: console

      sed -i -e 's,/old/scanroot/,/path/to/new/scanroot/,g' /tmp/dump.json

7. Restore database in new marv:

   .. code-block:: console

      marv restore /tmp/dump.json

8. Set password for each user:

   .. code-block:: console

      marv user pw <username>

9. Run nodes:

   .. code-block:: console

      marv query -0 --collection=bags |xargs -0 -L25 -P4 marv run --keep-going

10. Run again sequentially to see if there are nodes producing errors:

   .. code-block:: console

      marv run --collection=bags
