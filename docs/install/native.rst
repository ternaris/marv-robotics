.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _install_native:

Native
======

Prerequisites
-------------

- Checkout of MARV Robotics Enterprise Edition or `Community Edition
  <https://github.com/ternaris/marv-robotics>`_


System dependencies
-------------------

MARV Robotics needs Python 3.8 and ships all components to open bag files and process ROS messages (ROS1 and ROS2). On top of Ubuntu focal ROS1 and ROS2 releases are available using Python 3.8. Please let us know if you experience any issues or need support for an older version of Python.

Ubuntu focal
^^^^^^^^^^^^

In general, MARV Robotics works on any Linux system. For Ubuntu focal the following will install the necessary system dependencies.

.. code-block:: console

   # apt-get install capnproto \
                     curl \
                     ffmpeg \
                     libcapnp-dev \
                     libffi-dev \
                     libfreetype6-dev \
                     libjpeg-dev \
                     liblz4-dev \
                     libpng-dev \
                     libssl-dev \
                     libz-dev \
                     python3.8 \
                     python3.8-dev \
                     python3.8-venv



MARV Robotics
-------------

For the following commands we assume you are within the directory of your checkout of MARV Robotics.

Setup MARV Robotics in Python virtual environment and activate it:

.. code-block:: console

  $ ./scripts/setup-venv requirements/marv-robotics.txt venv
  $ source venv/bin/activate
  (venv) $ marv --help

Et voilà, marv is successfully installed. The ``(venv)`` prefix indicates the activated virtualenv. In the following sections we assume that your virtualenv is activated. If ``marv`` cannot be found, chances are that the virtualenv containing MARV Robotics is not activated.  For more information see `Virtual Environments <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.

.. warning::

   MARV Robotics does not need write access to your bag files. As a safety measure install and run MARV as a user having only read-only access to your bag files.


Build and serve documentation
-----------------------------

Let's dedicate a terminal to build the documentation and to start a small webserver to serve the documentation; actually, to serve MARV Robotics already, which contains the documentation.

.. code-block:: console

   (venv) $ ./scripts/build-docs
   (venv) $ marv --config tutorial/docs-only-site/marv.conf serve

Now you have an instance of MARV running at: http://localhost:8000.

It's documentation is linked in the footer and served at: http://localhost:8000/docs/

Let's switch to your `locally served documentation <http://localhost:8000/docs/install/native.html#build-and-serve-documentation>`_.


Summary
-------

You installed some system dependencies, created a virtual python environment, installed MARV Robotics into it, and started a webserver with marv and its documentation:

Now you are ready to `setup a basic site <../tutorial/setup-basic-site.html>`_.
