.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _setup-basic-site:

Tutorial: Setup basic site
==========================

A site holds everything MARV knows about your datasets. It contains one or more collections of datasets that can be browsed and queried separately. Here you learn how to setup a basic site with one collection and a couple of example bags.

All code and configuration of this tutorial is included in the top-level ``tutorial`` folder of your MARV Robotics checkout.


Prerequisites
-------------

- :ref:`install`


Initialize site
---------------

Let's start by creating a directory that will hold bag files, called a *scanroot*, and one for our marv site:

.. code-block:: console

  $ mkdir site
  $ mkdir site/scanroot

Then create the site configuration file ``site/marv.conf`` with the following content:

.. literalinclude:: setup-basic-site0/marv.conf
    :language: cfg

There is one collection that uses marv robotics' default bag scanner :func:`marv_robotics.bag.scan`, which is looking for bags in the scanroot we just created. We are ready to initialize the site -- after activating the virtual environment marv is installed to, and simplifying marv's log format as we are not interested in times:

.. code-block:: console

  $ source venv/bin/activate
  (venv) $ export MARV_LOG_FORMAT='%(levelname).4s %(name)s %(message)s'
  (venv) $ cd site
  (venv:~/site) $ marv init
  INFO marv.site Initialized from /home/zaphod/site/marv.conf

.. note::

   Whenever you change your configuration, remember to stop ``marv serve`` (see
   below), rerun ``marv init``, and then start ``marv serve`` again.

**docker**:

Tell container to run ``marv init`` and install all code in development mode.

.. code-block:: console

   $ MARV_INIT=1 DEVELOP=1 ./scripts/run-container site site/scanroot


Serve the site
--------------

The MARV backend is implemented using the asynchronous HTTP client/server framework `aiohttp <https://github.com/aio-libs/aiohttp>`_ and is by default served using the Python WSGI HTTP Server `Gunicorn <https://gunicorn.org>`_.  MARV internally wraps Gunicorn through the MARV cli ``server`` subcommand. If you followed the installation instructions, the page you are looking at is already being served by MARV. When run without any options MARV will try to find a ``marv.conf`` in the current directory. You can also point MARV to serve a specific site using:

.. code-block:: console

  CTRL-C
  (venv) $ marv serve --config site/marv.conf
  ...
  [2019-08-15 14:48:03 +0200] [8255] [INFO] Starting gunicorn 19.9.0
  [2019-08-15 14:48:03 +0200] [8255] [INFO] Listening at: http://0.0.0.0:8000 (8255)
  [2019-08-15 14:48:03 +0200] [8255] [INFO] Using worker: aiohttp.GunicornUVLoopWebWorker
  [2019-08-15 14:48:03 +0200] [8258] [INFO] Booting worker with pid: 8258
  [2019-08-15 14:48:03 +0200] [8259] [INFO] Booting worker with pid: 8259
  [2019-08-15 14:48:03 +0200] [8260] [INFO] Booting worker with pid: 8260
  [2019-08-15 14:48:03 +0200] [8261] [INFO] Booting worker with pid: 8261

You should see something like the above lines and MARV should be accessible via http://localhost:8000. In case you are running inside a container, make sure you forwarded the correct port.


.. note::

   In the course of this tutorial we'll keep changing the configuration. For these changes to take effect, ``marv serve`` has to be stopped (CTRL-C) and the site reinitialized with ``marv init``.


**docker**:

Restart container.

.. code-block:: console

   $ MARV_INIT=1 DEVELOP=1 ./scripts/run-container site site/scanroot
   CTRL-C
   $ MARV_INIT=1 DEVELOP=1 ./scripts/run-container site site/scanroot



Create user account
-------------------

MARV requires you to be signed-in to see anything worthwhile. In order to be able to sign-in, you need to create a user first. Let's make him an admin, so he can also discard datasets from marv. From now on we can continue in the terminal we used to initialize the marv site previously:

.. code-block:: console

  (venv:~/site) $ marv user add zaphod
  Password:
  Repeat for confirmation:
  (venv:~/site) $ marv group adduser zaphod admin

After creating the user, you should be able to sign-in using his credentials and be presented with an yet empty listing of the bags collection.

.. note::

   You can change the access control list, to allow for example public access to MARV (see :ref:`cfg_marv_acl`).

**docker**: Run commands inside container, after entering it with ``./scripts/enter-container``.

.. code-block:: console

   $ ./scripts/enter-container
   $ marv user add zaphod
   Password:
   Repeat for confirmation:
   $ marv group adduser zaphod admin


Populate scanroot
-----------------

Let's give marv two bag files from the `mit stata center data set <http://projects.csail.mit.edu/stata/downloads.php>`_:

.. code-block:: console

  (venv:~/site) $ cd scanroot
  (venv:~/site/scanroot) $ curl -O http://infinity.csail.mit.edu/data/2011/2011-01-24-06-18-27.bag
  (venv:~/site/scanroot) $ curl -O http://infinity.csail.mit.edu/data/2011/2011-01-25-06-29-26.bag
  (venv:~/site/scanroot) $ cd -
  (venv:~/site) $

After scanning for datasets they will appear in the bag collection's listing:

.. code-block:: console

  (venv:~/site) $ marv scan
  INFO marv.collection.bags added <Dataset qmflhjcp6j3hsq7e56xzktf3yq 2011-01-24-06-18-27>
  INFO marv.collection.bags added <Dataset vmgpndaq6frctewzwyqsrukg2y 2011-01-25-06-29-26>

The *dataset ids*, or short *set ids*, are generated randomly -- you will see different ones. If not, watch out for the Heart of Gold. Now, reload the browser. The listing should contain the two datasets. Visiting a detail view, there is no information yet, but after logging in it's already possible to comment and tag the datasets.

**docker**: Run commands inside container, after entering it with ``./scripts/enter-container``.


Add and run basic nodes
-----------------------

MARV ships with some default nodes. Let's run these:

.. code-block:: console

  (venv:~/site) $ marv run --collection=bags
  INFO marv.run qmflhjcp6j.meta_table.dwz4xbykdt.default (meta_table) started
  INFO marv.run qmflhjcp6j.summary_keyval.dwz4xbykdt.default (summary_keyval) started
  INFO marv.run qmflhjcp6j.summary_keyval.dwz4xbykdt.default finished
  INFO marv.run qmflhjcp6j.meta_table.dwz4xbykdt.default finished
  INFO marv.run vmgpndaq6f.meta_table.dwz4xbykdt.default (meta_table) started
  INFO marv.run vmgpndaq6f.summary_keyval.dwz4xbykdt.default (summary_keyval) started
  INFO marv.run vmgpndaq6f.summary_keyval.dwz4xbykdt.default finished
  INFO marv.run vmgpndaq6f.meta_table.dwz4xbykdt.default finished

By now the detail summary section is providing minimal information.

Given that we are dealing with bag files, it makes sense to add nodes that extract and display bag meta information:

.. literalinclude:: setup-basic-site1/marv.conf
    :language: cfg
    :emphasize-lines: 9-

.. code-block:: console

  (venv:~/site) $ marv run --collection=bags
  INFO marv.run qmflhjcp6j.bagmeta_table.gahvdc4vpg.default (bagmeta_table) started
  INFO marv.run qmflhjcp6j.connections_section.yjrewalqzc.default (connections_section) started
  INFO marv.run qmflhjcp6j.bagmeta.dwz4xbykdt.default (bagmeta) started
  INFO marv.run qmflhjcp6j.bagmeta.dwz4xbykdt.default finished
  INFO marv.run qmflhjcp6j.connections_section.yjrewalqzc.default finished
  INFO marv.run qmflhjcp6j.bagmeta_table.gahvdc4vpg.default finished
  INFO marv.run vmgpndaq6f.bagmeta_table.gahvdc4vpg.default (bagmeta_table) started
  INFO marv.run vmgpndaq6f.connections_section.yjrewalqzc.default (connections_section) started
  INFO marv.run vmgpndaq6f.bagmeta.dwz4xbykdt.default (bagmeta) started
  INFO marv.run vmgpndaq6f.bagmeta.dwz4xbykdt.default finished
  INFO marv.run vmgpndaq6f.connections_section.yjrewalqzc.default finished
  INFO marv.run vmgpndaq6f.bagmeta_table.gahvdc4vpg.default finished

Reload your browser and check the result.

**docker**: Run commands inside container, after entering it with ``./scripts/enter-container``.


Summary
-------

You initialized a marv site with one collection that looks for bag files in a scanroot directory. You setup Gunicorn to serve your site for development purposes, created a user account for sign-in to the web application, populated the scanroot with some bag files and configured and ran nodes to display meta information about these bag files.

Familiarize yourself a bit with the web frontend (http://localhost:8000). We intend it to be self-explanatory. Please let us know if you have questions.

Now your are ready to write your first nodes :ref:`write-your-own`.
