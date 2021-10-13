.. Copyright 2016 - 2021  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _migrate:

Migration
=========

Listed here are all versions that necessitate migration. Depending on the version you are migrating from you might need to follow multiple migration steps.

In case of database migrations it is sufficient to ``marv dump`` the database with the version you are currently using and ``marv restore`` with the latest version; marv is able to *dump* itself and *restore* any older version. In case this does not hold true ``marv restore`` will complain and provide instructions what to do.


.. _migrate-21.10.0:

21.10.0
-------
Previously MARV shipped a fork of the upstream rosbag Python library for ROS1 bag reading and writing. These tasks are now handled by `rosbags`_ which offers better performance and a unified interface for ROS1 and ROS2 bags. One of the main user facing changes is that ROS1 message type names are now normalized to their ROS2 counterparts. While searching a database with ROS1 and ROS2 bags for images required filtering for message type ``sensor_msgs/Image`` **and** ``sensor_msgs/msg/Image`` in the past, the same query is now achieved just by filtering for ``sensor_msgs/msg/Image``.

.. _rosbags: https://gitlab.com/ternaris/rosbags

Bagmeta node for ROS1 bags needs to be rerun
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Rerun the node ``marv_robotics.bag:bagmeta`` to get normalized message type names:

.. code-block:: console

   marv run --col="*" --force \
     --node bagmeta \
     --node summary_keyval \
     --node bagmeta_table \
     --node connections_section


Stop using classic ROS1 message type names
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Update any code or API calls using classic ROS1 message type names to the corresponding ROS2 names.


Update any code using get_message_type()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
MARV nodes now have access to rosbag version agnostic types, you need to update your type deserialization code.

Replace the pattern

.. code-block:: python

   from marv_robotics.bag import get_message_type
   ...
   rosmsg = get_message_type(stream)() if stream.msg_type else None
   ...
   rosmsg.deserialize(msg.data)

with

.. code-block:: python

   from marv_robotics.bag import make_deserialize
   ...
   deserialize = make_deserialize(stream)
   ...
   rosmsg = deserialize(msg.data)



.. _migrate-21.07.0:

21.07.0
-------

Switch to rosbags library
^^^^^^^^^^^^^^^^^^^^^^^^^
Previously MARV shipped with a builtin ROS2 bag reader. Out of the box it supported deserialization of all default ROS2, Autoware.Auto, and automotive_autonomy messages. The ROS2 reading code was spun off into `rosbags`_. To allow for more flexibility in regards to type versioning, rosbags includes a dynamic type system that can be extended during runtime and does only include ROS2 default messages.

If you are using the previously included messages in your ROS2 bags, you have to provide their message definitions to MARV with the following commands in your site folder:

.. code-block:: console

   mkdir -p resources/messages
   cd resources/messages
   git clone https://gitlab.com/autowarefoundation/autoware.auto/autoware_auto_msgs.git
   git clone https://github.com/astuff/automotive_autonomy_msgs.git

.. _rosbags: https://gitlab.com/ternaris/rosbags


Connections_section migration (EE)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The EE node ``marv_ee_nodes.detail:connections_section`` has gained support for the download of time slices. On installations that use this node its output needs to be regenerated:

.. code-block:: console

   marv run --force --node connections_section --col=\*


.. _migrate-21.05.0:

21.05.0
-------

Code migration
^^^^^^^^^^^^^^
- Removed deprecated marv.types, use marv_api.types instead
- Removed deprecated marv.utils.popen, use marv_api.utils.popen instead
- Removed deprecated HTTP listing API, query :ref:`httpapi_query_collection` instead
- Removed deprecated list config function, use makelist instead


Configuration migration (CE)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``acl`` configuration key for setting a route-based permission profile was removed. If you were previously using the ``marv_webapi.acls:public`` profile in your CE installation, you can grant anonymous users readonly access with the :ref:`cfg_marv_ce_anonymous_readonly_access` configuration key.


Database migration
^^^^^^^^^^^^^^^^^^
Dataset and leaf permission management required changes to database schemas, a migration of the MARV database is necessary. Export the database with your current version of MARV:

.. code-block:: console

   marv dump dump-2103.json
   mv db/db.sqlite db/db.sqlite.2103

After updating MARV run:

.. code-block:: console

   marv init
   marv restore dump-2103.json


.. _migrate-21.03.0:

21.03.0
-------

Database migration
^^^^^^^^^^^^^^^^^^
Extended user and leaf management, among others, required changes to database schemas, a migration of the MARV database is necessary. Export the database with your current version of MARV:

.. code-block:: console

   marv dump dump-2012.json
   mv db/db.sqlite db/db.sqlite.2012

After updating MARV run:

.. code-block:: console

   marv init
   marv restore dump-2012.json


Leaves storage configuration changes (EE)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
MARV now uses a dedicated directory to store datasets uploaded by leaves (default ``./leaves`` in your site). Update your reverse proxy configuration to serve these files. For nginx add:

.. code-block:: nginx

       location /docker/container/path/to/leavesdir {
         internal;
         alias /host/path/to/leavesdir;
       }

See also :ref:`deploy_nginx`.


.. _migrate-20.12.0:

20.12.0
-------

Database migration
^^^^^^^^^^^^^^^^^^
Extended RPC filters, among others, required changes to database schemas, a migration of the MARV database is necessary. Export the database with your current version of MARV:

.. code-block:: console

   marv dump dump-2008.json
   mv db/db.sqlite db/db.sqlite.2008

After updating MARV run:

.. code-block:: console

   marv init
   marv restore dump-2008.json


Code migration (CE)
^^^^^^^^^^^^^^^^^^^
Node :func:`marv_robotics.trajectory.navsatfix` now returns timestamps as integer in nanoseconds instead of as float in seconds. Directly consuming custom nodes need migration, all nodes shipping with marv are already adjusted accordingly.


Config migration (EE)
^^^^^^^^^^^^^^^^^^^^^
To implement partial downloads, the Enterprise Edition now uses a dedicated connections section. Please adjust your config accordingly and rerun the corresponding node:

.. code-block:: diff

   -    marv_robotics.detail:connections_section
   +    marv_ee_nodes.detail:connections_section


.. code-block:: console

   marv run --force --node connections_section --col=\*



.. _migrate-20.08.0:

20.08.0
-------

Session key file
^^^^^^^^^^^^^^^^

A marv site contains a session key file used in authenticating marv users. This file was previously readable by all users of the host system. We recommend to delete the file and restart marv to recreate it automatically. All marv users will have to relogin.

.. code-block:: sh

   rm site/sessionkey


Table column sorting
^^^^^^^^^^^^^^^^^^^^
Table columns containing links use dictionaries instead of plain values and the sort order of these will seem random. Use ``sortkey`` on table columns to define the dictionary key for sorting (see :ref:`widget_table` for more information).

In case you are using :func:`marv_robotics.detail.bagmeta_table` and have datasets with multiple files, you might want to run:

.. code-block:: sh

   marv run --node bagmeta_table --force --col=*

Likewise for :func:`marv_nodes.meta_table`.


.. _migrate-20.06.0:

20.06.0
-------

Changes to access control
^^^^^^^^^^^^^^^^^^^^^^^^^
MARV supports access control profiles that dictate who is permitted to perform what. Profiles map actions like ``comment`` or ``tag`` to lists of user groups that are permitted to perform these actions. This version of MARV cleans up and streamlines the list of supported verbs.

If you created a custom profile, please refer to ``marv_webapi.acls`` as an example and make sure to adjust your custom profile to use the new action verbs.

No migration is necessary for installations that use one of the two default profiles (``authenticated`` or ``public``).


Database migration
^^^^^^^^^^^^^^^^^^
Changes to collection management required changes to database schemas. A migration of the MARV database is necessary. Export the database with your current version of MARV:

.. code-block:: console

   marv dump dump-2004.json
   mv db/db.sqlite db/db.sqlite.2004

After updating MARV run:

.. code-block:: console

   marv init
   marv restore dump-2004.json


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

MARV now supports access control lists (ACLs). The default ACL requires authentication to read anything, tag and comment; and only members of the group admin may discard datasets. For users of the Enterprise Edition this corresponds to the same behaviour as before.


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
