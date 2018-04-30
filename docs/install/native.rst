.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _install_native:

Native
======

MARV Robotics is implemented in Python using the MARV framework. Most of its Python dependencies will be installed via Python's package management tools. Apart from these, ROS and some system libraries need to be installed, as outline in the following section.

Prerequisites
-------------

*EE*:

- `Robot Operating System (ROS) <http://wiki.ros.org/ROS/Installation>`_
- Checkout of your release of MARV Robotics EE

.. code-block:: console

  $ ls -1
  marvee  # checkout of your MARV Robotics EE
  $ ln -s marvee/requirements.txt .
  $ ln -s marvee/code/marv/docs/tutorial .
  $ ls -1
  marvee
  requirements.txt
  tutorial

*CE*

- `Robot Operating System (ROS) <http://wiki.ros.org/ROS/Installation>`_
- Checkout of https://github.com/ternaris/marv

.. code-block:: console

  $ ls -1
  marv  # checkout of marv community edition
  $ curl -LO https://raw.githubusercontent.com/ternaris/marv-robotics/master/requirements.txt
  $ ln -s marv/docs/tutorial .
  $ ls -1
  marv
  requirements.txt
  tutorial


.. _ros-install:

Robot Operating System
----------------------

We assume you have working installation of ROS installed. MARV Robotics is meant to support all alive ROS releases (starting with kinetic). If you encounter difficulties with these, please report back!

We dropped support for Indigo due to outdated system dependencies that cannot be easily upgraded. If you need indigo support please let us know.

On an Ubuntu system the following are needed (as root). In case you succeeded installing ROS on anything else than Ubuntu, we trust you'll also succeed to transfer the following lines to the system you are installing to.


Kinetic
^^^^^^^

.. code-block:: console

   # apt-get install capnproto \
                     curl \
                     ffmpeg \
                     libcapnp-dev \
                     libjpeg-dev \
                     libz-dev \
                     python-cv-bridge \
                     python2.7-dev \
                     python-opencv \
                     python-virtualenv \
                     ros-kinetic-laser-geometry \
                     ros-kinetic-ros-base
   ...
   # rosdep init

Make sure ROS is set-up correctly for your user (not as root):

.. code-block:: console

   $ rosdep update
   $ source /opt/ros/kinetic/setup.bash


.. _marv-install:

MARV Robotics
-------------

MARV Robotics is a Python application. For increased reproducability of installations we use a virtual python environment and a set of frozen requirements for installation.

Create virtualenv
^^^^^^^^^^^^^^^^^

Create a Python virtual environment, activate it and update its package management tools:

.. code-block:: console

  $ virtualenv -p python2.7 --system-site-packages venv
  $ source venv/bin/activate
  $ pip install -U pip setuptools pip-tools

Test whether ROS is available from within the activated virtualenv, as a result of the ``--system-site-packages`` option. The ``(venv)`` prefix indicates the activated virtualenv:

.. code-block:: console

  (venv) $ python -c 'import rosbag; print("rosbag available")'
  rosbag available

For more information see `Virtual Environments
<http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.


Install requirements
^^^^^^^^^^^^^^^^^^^^
Let's synchronize the virtual environment to exactly those packages we want.

.. code-block:: console

  (venv) $ pip-sync requirements.txt

.. warning::

   ``pip-sync`` will remove everything from the virtual environment that is not mentioned in ``requirements.txt``! That is not an issue if you use it only for marv as outlined in this installation manual.


Install MARV Robotics
^^^^^^^^^^^^^^^^^^^^^

*EE*:

.. code-block:: console

  (venv) $ pip install --no-index --find-links='' marvee/code/*

*CE*:

.. code-block:: console

  (venv) $ pip install marv-robotics

Verify MARV Robotics is successfully installed:

.. code-block:: console

  (venv) $ marv --help

``marv --help`` should print marv's usage instructions. In the following sections we assume that your virtualenv is activated. If ``marv`` cannot be found, chances are that the virtualenv containing MARV Robotics is not activated.


Serve documentation
-------------------

Let's dedicate a terminal to start a small webserver to serve the documentation. Actually, to serve MARV Robotics EE already, which contains the documenation.

.. code-block:: console

  (venv) $ uwsgi --ini tutorial/docs-only-site/uwsgi-dev.conf

Now you have an instance of MARV running at: http://localhost:8000.

It's documentation is linked in the footer and served at: http://localhost:8000/docs/

If you are running marv inside a container, make sure port 8000 is forwarded to outside the container.

Let's switch to your `locally served documentation <http://localhost:8000/docs/install.html#serve-documentation>`_.


Summary
-------

Based on an existing ROS installation, you installed some system dependencies, created a virtual python environment, installed MARV Robotics EE into it, and started a webserver with marv and its documentation:

.. code-block:: console

  $ ls -1
  ...
  tutorial  # link to tutorial directory
  venv      # python virtualenv

Now your are ready to `setup a basic site <./tutorial/setup-basic-site.html>`_.
