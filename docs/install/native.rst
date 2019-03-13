.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _install_native:

Native
======

MARV Robotics is implemented in Python using the MARV framework. Most of its Python dependencies will be installed via Python's package management tools. Apart from these, ROS and some system libraries need to be installed, as outlined in the following section.


Prerequisites
-------------

- `Robot Operating System (ROS) <http://wiki.ros.org/ROS/Installation>`_
- Checkout of MARV Robotics Enterprise Edition or `Community Edition <https://github.com/ternaris/marv-robotics>`_


Robot Operating System
----------------------

We assume you have working installation of ROS. MARV Robotics is meant to support all alive ROS releases (starting with kinetic). If you encounter difficulties with these, please report back!

We dropped support for Indigo due to outdated system dependencies that cannot be easily upgraded. If you need indigo support please let us know.

On an Ubuntu system the following are needed (as root). In case you succeeded installing ROS on anything else than Ubuntu, we trust you'll also succeed to transfer the following lines to the system you are installing to.


Kinetic
^^^^^^^

.. code-block:: console

   # apt-get install capnproto \
                     curl \
                     ffmpeg \
                     libcapnp-dev \
                     libffi-dev \
                     libfreetype6-dev \
                     libjpeg-dev \
                     libpng-dev \
		     libssl-dev \
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


MARV Robotics
-------------

MARV Robotics is a Python application `published on PyPI <https://pypi.org/project/marv-robotics/>`_ and a simple ``pip install marv-robotics`` should get you going. However, for increased reproducibility of installations we use and recommend a virtual python environment and a set of frozen requirements.

For the following commands we assume you are within the directory of your checkout of MARV Robotics.

Setup MARV Robotics in Python virtual environment and activate it:

.. code-block:: console

  $ ./scripts/setup-venv requirements.txt venv
  $ source venv/bin/activate
  (venv) $ marv --help

Et voilà, marv is successfully installed. The ``(venv)`` prefix indicates the activated virtualenv. In the following sections we assume that your virtualenv is activated. If ``marv`` cannot be found, chances are that the virtualenv containing MARV Robotics is not activated.
For more information see `Virtual Environments <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.

.. warning::
   MARV Robotics does not need write access to your bag files. As a
   safety measure install and run MARV as a user having only read-only
   access to your bag files.


Build and serve documentation
-----------------------------

Let's dedicate a terminal to build the documentation and to start a small webserver to serve the documentation; actually, to serve MARV Robotics already, which contains the documentation.

.. code-block:: console

   (venv) $ ./scripts/build-docs
   (venv) $ uwsgi --ini tutorial/docs-only-site/uwsgi-dev.conf

Now you have an instance of MARV running at: http://localhost:8000.

It's documentation is linked in the footer and served at: http://localhost:8000/docs/

Let's switch to your `locally served documentation <http://localhost:8000/docs/install/native.html#build-and-serve-documentation>`_.


Summary
-------

Based on an existing ROS installation, you installed some system dependencies, created a virtual python environment, installed MARV Robotics into it, and started a webserver with marv and its documentation:

Now you are ready to `setup a basic site <../tutorial/setup-basic-site.html>`_.
