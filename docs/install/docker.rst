.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _install_docker:

Docker
======

Prerequisites
-------------

- `Docker <https://www.docker.com/>`_ version 18.03.1-ce or greater, it might work with older versions as well.
- Checkout of MARV Robotics Enterprise Edition or `Community Edition <https://github.com/ternaris/marv-robotics>`_


Building or configure image used
--------------------------------

Users of the Enterprise Edition build their own image based on their custom release of MARV Robotics EE. Users of the Community Edition can use the published MARV Robotics CE Image ``ternaris/marv-robotics`` or build their own.


Enterprise Edition and custom image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Building your own image is as simple as running ``./scripts/build-image``.

::

   $ ./scripts/build-image
   ...
   Successfully tagged marvee-marvhub:latest

The basename of your checkout of MARV Robotics will be used as image name and subsequently also as container name. That way it is possible to have multiple containers based on different images running side-by-side.


Community Edition: Official MARV Robotics CE Image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to use the official MARV Robotics Community Edition image instead, the scripts contained in the repository have to be instructed accordingly.

::

   $ cd marv-robotics
   $ echo ternaris/marv-robotics > .image-name


Start container
---------------

Run container provides instructions for the basic use case.

::

   $ ./scripts/run-container

   Usage: run-container SITE SCANROOT [EXTRA_OPTS ...]

   The site is expected to contain marv.conf and gunicorn_cfg.py.
   It is mounted inside the container at /home/marv/site.

   The scanroot contains the log files for one or more collections.
   It is mounted read-only into the container at /scanroot.

   All additional arguments are passed as options to docker run.

Without further arguments it will run the container in the foreground, which is good for development where you want to kill and recreate it occasionally.

::

   $ ./scripts/run-container sites/example path/to/scanroot

Use ``--detach`` to start the container in the background.

::

   $ ./scripts/run-container sites/example path/to/scanroot --detach

Either way, you can enter the running container.

::

   $ ./scripts/enter-container
   marv@ce:~$ marv --help

The scanroot is mounted read-only as ``/scanroot`` inside the container. Be aware of that when creating your own configuration.


Adding your own code
--------------------

To add your own code, create a python package in ``./code`` next to the marv packages. When building an image, all of the code is copied into the image and installed automatically. Especially during development, you don't want to rebuild all the time.

::

   MARV_INIT=1 DEVELOP=1 ./scripts/run-container sites/example path/to/scanroot

In general changes you make to your code will be effective immediately. However, after adding the package, when making changes to its ``setup.py``, and when making changes affecting the web serving part of marv, the container needs to be restarted. As a rule of thumb: when you make changes to the config file, you want to restart using ``MARV_INIT=1``, while making changes to your node code does not need a restart.


Serve documentation
-------------------

While the container is running MARV Robotics should be available at: http://localhost:8000.

And it's documentation is linked in the footer and served at: http://localhost:8000/docs/

Let's switch to your `locally served documentation <http://localhost:8000/docs/install/docker.html#serve-documentation>`_.


Summary
-------

Using tooling from the MARV Robotics repository you created your own docker image or used the official CE image and started a docker container running marv.

Now you are ready to `setup a basic site <../tutorial/setup-basic-site.html>`_.
