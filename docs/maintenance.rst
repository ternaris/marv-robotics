.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _maintenance:

Maintenance
===========

Cleanup
-------

When datasets are discarded (via frontend, API, cli) they are only marked to be removed from marv's database and can be "undiscarded".

.. code-block:: bash

   marv undiscard --help

To actually remove these from the database

.. code-block:: bash

   marv cleanup --discarded

After deleting datasets manually from the filesystem, you can remove them from the database as follows:

.. code-block:: bash

   marv scan
   marv query --missing | xargs marv discard
   marv cleanup --discarded

When searching for ``subset`` :ref:`cfg_c_filters`, marv presents matching results, including values from meanwhile cleaned-up datasets. Cleanup these filters with:

.. code-block:: bash

   marv cleanup --filters

Additional cleanup operations will be added in one of the next releases.

Backup
------

By default, all data related to a marv site is stored in a site directory. It holds the following information:

- ``db`` marv's sqlite database
- ``marv.conf`` the marv configuration file
- ``sessionkey`` if it changes, users will have to relogin
- ``store`` of all node output, theoretically possible to recreate by running all nodes, which might not be feasible
- ``gunicorn_cfg.py`` configuration for gunicorn serving the marv application

Make sure to create regular backups of this site directory or the individual components in case you placed them elsewhere. It is not necessary to stop marv to create backups.


Dump/restore
------------

Use ``marv dump`` and ``marv restore`` to dump marv's database to a json format and to restore it in a site with the same configuration. You can use the latest version to dump older databases.

The dump contains:

  - datasets for all collections with setid, files, tags, and comments
  - and users with group memberships.

Apart from the dump, you need to copy from old site:

  - marv.conf
  - gunicorn_cfg.py
  - sessionkey (if it changes, users will have to relogin)
  - store (if you don't copy the store, all nodes will have to rerun)

.. code-block:: bash

   cd old-site
   marv dump ../dump.json

   cd ../new-site
   cp -a ../old-site/marv.conf ./
   cp -a ../old-site/gunicorn_cfg.py ./
   cp -a ../old-site/sessionkey ./
   cp -a ../old-site/store ./
   marv restore ../dump.json

**DUMP/RESTORE IS NOT A REPLACEMENT FOR MAKING BACKUPS**
