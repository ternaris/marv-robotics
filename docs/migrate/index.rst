.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _migrate:

Migration
=========

Before doing any migration you might want to check the :ref:`config` and :ref:`deploy` sections.


.. _migrate_18_07_to_19_02_0:

18.07 -> 19.02.0
----------------

Support for ipdb has been dropped in favour of `pdb++ <https://github.com/antocuni/pdb>`_. Use ``PDB=1 marv run`` instead of ``marv-ipdb run``. For more information see :ref:`debug`.


.. _migrate_18_05_to_18_07:

18.05 -> 18.07
--------------

The way inputs are handled has changed. Inputs selecting an individual topic are now optional. See :ref:`optional_inputs` for more information.


.. _migrate_18_03_to_18_04:

18.03 -> 18.04
--------------

The list of system dependencies is updated and the installation has significantly changed. We recommend that you re-read the :ref:`install` instructions. The database has not changed and existing sites continue to function without migration.

MARV now supports offloading the delivery of files to nginx. In case you are not using nginx as reverse-proxy, yet, you should seriously consider to change that now. See :ref:`cfg_marv_reverse_proxy` and :ref:`deploy_nginx`.

MARV now supports access control lists (ACLs). The default ACL requires authentication to read anything, tag and comment; and only members of the group admin may discard datasets. For users of the Enterprise Edition this corresponds to the same behaviour as before. The :func:`marv_webapi.acls.public` closely resembles the previous Community Edition default, apart from requiring admin group membership to discard datasets. See :ref:`cfg_marv_acl` to change the effective ACL.


.. _migrate_18_02_to_18_03:

18.02 -> 18.03
--------------

With this release:

- geojson property object has changed.

To update the store to the new format rerun the trajectory nodes using:

.. code-block:: console

   marv run --node trajectory --force --force-dependent --collection=*


.. _migrate_17_11_to_18_02:

17.11 -> 18.02
--------------

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


.. _migrate_16_10_to_17_11:

16.10 -> 17.11
--------------

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
