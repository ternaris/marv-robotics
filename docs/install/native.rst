.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _install_native:

Native
======

MARV Robotics is implemented in Python using the MARV framework. Most of its Python dependencies will be installed via Python's package management tools. Apart from these, ROS and some system libraries need to be installed, as outlined in the following section.


Prerequisites
-------------

- Checkout of MARV Robotics Enterprise Edition or `Community Edition
  <https://github.com/ternaris/marv-robotics>`_


System dependenices
-------------------

MARV Robotics needs Python 3.7 and ships all components to open bag files and process ROS messages. If you need any ROS libraries for your nodes, please let us know if we can assist making them available for Python 3.7.

Ubuntu bionic
^^^^^^^^^^^^^

In general, MARV Robotics works on any Linux system. For Ubuntu bionic the following will install the necessary system dependencies.

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
                     python3.7 \
                     python3.7-dev \
                     python3.7-venv


MARV Robotics
-------------

MARV Robotics is a Python application `published on PyPI <https://pypi.org/project/marv-robotics/>`_ and a simple ``pip install marv-robotics`` should get you going. However, for increased reproducibility of installations we use and recommend a virtual python environment and a set of frozen requirements.

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

Based on an existing ROS installation, you installed some system dependencies, created a virtual python environment, installed MARV Robotics into it, and started a webserver with marv and its documentation:

Now you are ready to `setup a basic site <../tutorial/setup-basic-site.html>`_.
