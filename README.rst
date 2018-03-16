=============
MARV Robotics
=============

Welcome to the MARV Robotics Community Edition.

MARV Robotics is a powerful and extensible data management platform, featuring a rich dynamic web interface, driven by your algorithms, configurable to the core, and integrating well with your tools to supercharge your workflows.

For more information please see:

- MARV Robotics `documentation <https://ternaris.com/marv-robotics/docs/>`_
- MARV Robotics `website <https://ternaris.com/marv-robotics/>`_


Quickstart
==========

Clone repository and tell scripts that you want to use the official MARV Robotics CE image. Alternatively, you can build it yourself with ``./scripts/build-image``, in which case you don't create the ``.image-name`` file.

::

   git clone git@github.com:ternaris/marv-robotics
   cd marv-robotics
   echo ternaris/marv-robotics > .image-name

Start container.

::

  ./scripts/run-container sites/example path/to/bags

There should be a couple of uwsgi workers waiting to serve requests and MARV Robotics is now running at: https://localhost:8000/

Additional arguments are passed as options to ``docker run``, e.g.

::

   ./scripts/run-container sites/example path/to/bags --detach

Enter the container, scan for datasets and run nodes.

::

   ./scripts/enter-container

::

   marv scan
   marv run --col=*

Add a user to add tags and comments.

::

   marv user add zaphod

Make the user a member of the admin group in order to discard datasets. With the next ``marv scan`` discarded datasets are re-added as new datasets; all data previously associated with them is deleted.

::

   marv group adduser zaphod admin

So far, only tooling and the example site are used from the repository.

For more information see our `Docker <https://ternaris.com/marv-robotics/docs/install/docker.html>`_ installation instructions.

Alternatively, you can follow the `Native <https://ternaris.com/marv-robotics/docs/install/native.html>`_ installation instructions.


Reporting issues / Minimal working example
==========================================

In order to provide a minimal working example to reproduce issues you are seeing, please:

1. Create a fork of this repository and clone it.
2. Create a site folder in `<./sites>`_ containing your configuration.
3. If there is custom code involved, please add a minimal working example based on it to a python package in `<./code>`_. We don't need to see your real code, but we cannot help without code.
4. Create a ``scanroot`` folder within your site folder and add minimal bags or other log files as needed.
5. Make sure the issues you are seeing are exposed by this setup.
6. Push your changes to your fork.
7. Create an issue in https://github.com/ternaris/marv-robotics/issues and add a link to the minimal working example.


