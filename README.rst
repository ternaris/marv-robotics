MARV Robotics (beta)
====================

MARV Robotics is an extensible data management platform for robot logs. New robot logs are found by a scanner and configured nodes are run to extract, filter and process data from them.

The robot logs are visualized in a web-based application that features a listing view with filters and summary, and detail views of individual log files.

So far MARV Robotics supports the Robot Operating System (ROS) Bag format used by systems running ROS to record sensor data and system state.


Robot Operating System (ROS)
----------------------------

MARV Robotics is meant to support all alive ROS releases. Currently these are indigo, jade, and kinetic -- if you encounter difficulties, please report back! The following instructions are written for ROS kinetic, adjust to your needs.


Requirements
------------

MARV Robotics is implemented in Python using the MARV framework. Most of its Python dependencies will be installed by pip automatically. Apart from these on an Ubuntu system the following are needed (as root)::

  # apt-get install curl \
                    ros-kinetic-ros-base \
                    python2.7-dev \
                    python-cv-bridge \
                    python-opencv \
                    python-virtualenv \
                    libjpeg-dev \
                    libz-dev
  # rosdep init

In case you succeeded installing ROS on anything else than Ubuntu, you'll also succeed to transfer above lines to the system you are installing to.

Make sure ROS is set-up correctly for your user (not as root)::

  $ rosdep update
  $ source /opt/ros/kinetic/setup.bash


Installation
------------

While strictly speaking a virtual Python environment is not necessary and MARV Robotics installs fine without, we highly recommend it.  For instructions to install into your user's home instead, see below.

Option 1: Virtual Python Environment (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Create a virtual environment and activate it::

  $ virtualenv -p python2.7 --system-site-packages venv
  $ source venv/bin/activate

Test whether ROS is available from within the activated virtualenv. The ``(venv)`` prefix indicates the activated virtualenv::

  (venv) $ python -c 'import rosbag; print("rosbag available")'
  rosbag available

For more information on virtualenvs see `Virtual Environments
<http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.

Install MARV Robotcs::

  (venv) $ pip install marv-robotics
  ...
  (venv) $ marv --help

``marv --help`` should print marv's usage instructions. In the following sections we assume that your virtualenv is activated. If ``marv`` cannot be found, chances are that the virtualenv containing MARV Robotics is not activated.


Option 2: User install
~~~~~~~~~~~~~~~~~~~~~~

An alternative to install into an isolated virtualenv (see above) is to install into the user's ``$HOME/.local`` folder where MARV Robotics might interfere with other installed programs. First check whether ``$HOME/.local/bin`` is in ``$PATH`` and ``$HOME/.local/lib/python2.7/site-packages`` in ``$PYTHONPATH``::

  $ echo $PATH
  $ echo $PYTHONPATH

and add if needed::

  $ export PATH="$HOME/.local/bin:$PATH"
  $ export PYTHONPATH="$HOME/.local/lib/python2.7/site-packages:$PYTHONPATH"

Verify that ROS is still available::

  $ python -c 'import rosbag; print("rosbag available")'
  rosbag available

Install MARV Robotics and verify it is available by printing its usage instructions::

  $ pip install --user marv-robotics
  ...
  $ marv --help
  ...

By now MARV Robotics should be successfully installed.


Configuration
-------------

After having successfully installed MARV Robotics, we can initialize a site that is going to hold configuration files and databases::

  (venv) $ marv init ./site
  Path to scanroot containing bags: /scanroot
  Application root for MARV, if not at root of domain []: 
  Wrote config file site/marv.conf
  Wrote site/wsgi.py
  Wrote site/uwsgi.conf

First marv will prompt for the scanroot, the location of your bag files. By default MARV Robotics is expected to be served at the root of a domain (e.g. http://localhost:8000/), specify an application root to server e.g. at ``/marv-robotics`` instead.

Take a look at the generated ``marv.conf``, it contains many comments and aims to compensate for the current lack of documentation.

**If your bags are dear to you, you should keep them read-only for the user running marv, write-access to anything within the scanroot is not needed and discouraged.**

If not specified otherwise, marv looks for the config file in the current directory, a bit like git. Let's changed into the site::

  (venv) $ cd site
  (venv) ~/site $


User management
---------------

In order to comment and tag through the web, marv user accounts are needed. The password will be prompted for::

  (venv) ~/site $ marv user add test
  Password: 
  Repeat for confirmation: 

The currently ensuing gibberish can be safely ignored.

Passwords are changed with::

  (venv) ~/site $ marv user pw test
  Password: 
  Repeat for confirmation:


Start webserver
---------------

MARV Robotics is implemented as a Python WSGI application. To serve it a WSGI server is needed, e.g. uWSGI. A configuration file was created previously by ``marv init`` within the marv site::

  (venv) ~/site $ pip install uwsgi
  ...
  (venv) ~/site $ uwsgi --ini uwsgi.conf

By now you should be able to visit your MARV Robotics installation with a web browser at http://localhost:8000/. So far no filesets have been scanned.


Scanning filesets and running nodes
-----------------------------------

Through scanning the scanroot marv detects new and changed filesets::

  (venv) ~/site $ marv fileset scan
  ...

Reloading your browser page should give you a list with detected filesets. Instead of proper names, UUIDs are displayed and there is not much to see yet in the detail view. However, when signed-in you could start to tag and comment already.

In general all ``*.bag`` files found in the scanroot are added. If you want ignore certain subtrees, add a ``.marvignore`` file::

  # touch /scanroot/ignored/.marvignore

In order to get more catchy names to be displayed for your bag sets, run the ``bagset_name`` node::

  (venv) ~/site $ marv node run --all-filesets --node bagset_name

and reload your browser. A list of nodes is produced by::

  (venv) ~/site $ marv node list

or simply run all configured nodes::

  (venv) ~/site $ marv node run --all-filesets --all-nodes


Integration with other tools
----------------------------

MARV Robotics integrates well with other tools through its `json api <http://jsonapi.org/>`_. To query all filesets having "gps" in their name use::

  $ curl -G -H "Accept: application/vnd.api+json" \
      http://localhost:8000/marv/api/2/listing \
      -d 'filter[objects]=[{"name":"name","op":"like","val":"%gps%"}]'

or with python requests::

  import requests
  import json

  url = 'http://127.0.0.1:8000/marv/api/2/listing'
  headers = {'Accept': 'application/vnd.api+json'}

  filters = [dict(name='name', op='like', val='%gps%')]
  params = {'filter[objects]': json.dumps(filters)}

  response = requests.get(url, params=params, headers=headers)
  assert response.status_code == 200
  print(response.json())

For more information see `flask-restless docs <http://flask-restless.readthedocs.io/en/1.0.0b1/fetching.html>`_, which is also the base for these examples.


Run tests and coverage
----------------------

So far MARV ships with some tests and more will follow for MARV and MARV Robotics before the final 2.0.0. release. You can simply run the tests::

  (venv) $ nosetests venv/lib/python2.7/site-packages/{marv,marv_robotics}

or produce a coverage report::

  (venv) $ nosetests --with-coverage \
                     --cover-branches \
                     --cover-erase \
                     --cover-html \
                     --cover-package marv \
                     --cover-package marv-robotics \
                     --cover-tests \
                     venv/lib/python2.7/site-packages/{marv,marv_robotics}
  (venv) $ chromium cover/index.html

**You should not run these within your site directory**


Licensing
---------

MARV Robotics is built using the MARV framework. MARV Robotics is licensed under `Apache License 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_. MARV is available as Free and Open Source Software under `AGPLv3 <https://www.gnu.org/licenses/agpl-3.0.en.html>`_ and as part of MARV Robotics `Enterprise Edition <https://ternaris.com/marv-robotics/>`_ with custom licenses.
