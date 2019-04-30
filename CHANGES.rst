.. _changelog:

Changelog
---------

Our versioning scheme uses a two-digit year, a two-digit month, and a
release counter within month. Previously the release counter was
omitted when zero.

Changes necessitating migration reference the corresponding migration
section. References are only rendered correctly as part of the Sphinx
documentation. Within GitLab please find the migration document
`here <./docs/migrate/index.rst>`_.


.. _upcoming_changes:

Upcoming (unreleased)
^^^^^^^^^^^^^^^^^^^^^

Added
~~~~~

Changed
~~~~~~~

Deprecated
~~~~~~~~~~

Removed
~~~~~~~

Fixed
~~~~~

Security
~~~~~~~~


.. _v19_04_0:

19.04.0 (2019-04-30)
^^^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Contribution guide and workflow to accept contributions
- High-lighting of last visited dataset when returning from detail view to listing view
- Support display of dates and times in local time, server time, or UTC (EE)
- Option to filter on table columns (EE)
- Option to hide table columns (EE)
- Documentation for adding custom static frontend files
- Generation and validation of hashes for Python requirements
- Tests for CE merge requests as part of internal CI runs
- Filter types for float and int

Changed
~~~~~~~
- End-to-end tests run reliably (EE)
- Move to GitLab to consolidate tooling `#54 <https://gitlab.com/ternaris/marv-robotics/issues/54>`_
- Remove quickstart instructions from README in favour of normal installation instructions
- Mount scanroot readonly in docker container
- Manage requirements files in central location for ease of use
- Derive MARV package inter-dependencies from requirements files
- Upgrade Python tooling to latest versions
- Upgrade Python dependencies to latest versions
- Reformat changelog
- Improve error message in ffmpeg node when conversion fails

Fixed
~~~~~
- Include requirements.in files in Python source distributions
- Set default unit of timedelta filters to seconds `#58`_
- Hitting enter key in subset filter now applies filters
- Fix initial zoom level for maps with empty geometries
- Fix support for GeoJSON points in trajectory widget `#50 <https://gitlab.com/ternaris/marv-robotics/issues/50>`_
- Let trajectory node produce correct GeoJSON for segments with only one coordinate
- Fix filtering of date fields with greater than or equals operation
- Only display successfully converted videos in video detail section

Security
~~~~~~~~
- Upgrade pyyaml library for `CVE-2017-18342`_
- Upgrade requests library for `CVE-2018-18074`_

.. _#50: https://gitlab.com/ternaris/marv-robotics/issues/50
.. _#58: https://gitlab.com/ternaris/marv-robotics/issues/58
.. _CVE-2017-18342: https://nvd.nist.gov/vuln/detail/CVE-2017-18342
.. _CVE-2018-18074: https://nvd.nist.gov/vuln/detail/CVE-2018-18074


.. _v19_02_0:

19.02.0 (2019-02-09)
^^^^^^^^^^^^^^^^^^^^

Changed
~~~~~~~
- Improve frontend render performance
- Improve testing and deployment infrastructure
- Prepare migration to GitLab
- Unify versioning of frontend and Python packages
- Dropped ipdb in favour of pdbpp (see :ref:`migrate_18_07_to_19_02_0`)

Fixed
~~~~~
- Support unicode characters in filenames and rosbag string messages `#42`_, `#45`_
- Only call formatters for values other than None
- Add support for GeoJSON points to trajectory widget `#50`_
- Properly load and initialise custom widgets `#47`_
- Properly reset state of button to fetch file lists `#41`_

.. _#41: https://gitlab.com/ternaris/marv-robotics/issues/41
.. _#42: https://gitlab.com/ternaris/marv-robotics/issues/42
.. _#45: https://gitlab.com/ternaris/marv-robotics/issues/45
.. _#47: https://gitlab.com/ternaris/marv-robotics/issues/47
.. _#50: https://gitlab.com/ternaris/marv-robotics/issues/50


.. _v18_07:

18.07 (2018-07-22)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Document pattern for reducing multiple streams
- Add cli command for database dump and restore
- Add controls to adjust point cloud playback speed
- Support querying for datasets with missing files
- Support link widgets with download attribute

Changed
~~~~~~~
- Update Python dependencies, most notably latest pycapnp
- Support streams of individual topics as optional inputs `#25`_ (see :ref:`migrate_18_05_to_18_07`)

Fixed
~~~~~
- Allow fulltext node to be used while directly subscribing to string topics
- Document the need for configured nodes to define a schema
- Document the need for setting stream headers
- Improve cli exception handling and error messages for certain edge cases
- Reset graphical tag filters on collection switch
- Fix utm conversion for gnss node `#39`_
- Properly set and reset outdated state of datasets
- Consistently set cache control header to disable caching of all content

.. _#25: https://gitlab.com/ternaris/marv-robotics/issues/25
.. _#39: https://gitlab.com/ternaris/marv-robotics/issues/39


.. _v18_05_1:

18.05.1 (2018-05-11)
^^^^^^^^^^^^^^^^^^^^

Fixed
~~~~~
- Correct coordinate transformations for cached trajectories


.. _v18_05:

18.05 (2018-05-08)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Enable loading dataset node output in comparison views
- Support setting UID and GID for docker installation `#34`_

Changed
~~~~~~~
- Auto-initialise previously unintialised site upon start
- Set docker container timezone to host timezone
- Set default matplotlib backend to Agg, removing the need to set it manually

Fixed
~~~~~
- Better support for colour formats
- Add scanroot to documentation deploy example for NGINX
- Cleanup form submit handling `#31`_
- Fix native installation method for Community Edition `#36`_
- Fix loading of videos for Community Edition `#35`_
- Gracefully handle permission denied upon initialisation

.. _#31: https://gitlab.com/ternaris/marv-robotics/issues/31
.. _#34: https://gitlab.com/ternaris/marv-robotics/issues/34
.. _#35: https://gitlab.com/ternaris/marv-robotics/issues/35
.. _#36: https://gitlab.com/ternaris/marv-robotics/issues/36


.. _v18_04:

18.04 (2018-04-30)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Add command-line group management to Community Edition
- Support configuration of access control lists
- Add docker setup with example site

Changed
~~~~~~~
- Speed-up streaming of videos and point clouds with NGINX reverse-proxy
- Improve point cloud player controls
- Improve trajectory player controls
- Make styling of widgets more consistent
- Switch from nosetest to pytest and cleanup requirements
- Drop Bootstrap v3 in favour of slim custom Bootstrap v4 derivate
- Merge and cleanup individual repositories
- Installation methods have significantly changed, reinstall is recommended (see :ref:`migrate_18_03_to_18_04`)

Fixed
~~~~~
- Fix trajectory generation
- Fix erroneous self-referentiality of some capnp structs
- Fix color format for opencv bridge


.. _v18_03:

18.03 (2018-03-10)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Add more flexible GeoJSON properties to map widget
- Make marker geometry configurable on map widget
- Draw markers using last known heading on map in absence of explicit rotation values
- Document creation of custom capnp types
- Ship capnp types for atomic values and timed values
- Add, list, and remove comments via command-line

Changed
~~~~~~~
- Changed GeoJSON property object needs rerender (see :ref:`migrate_18_02_to_18_03`)

Fixed
~~~~~
- Display correct tags when paging in listing
- Render GeoJSON lines with correct width in Firefox
- Fix command-line tagging `#26`_
- Gnss node handles absence of valid GPS messages `#28`_
- Add missing int and float formatters
- Validate names for newly added users and groups
- Document disabling of uwsgi buffering to enable downloads larger than 1GB `#24`_
- Fix tags displayed in listing table for any but the first page `#27`_
- Fix documentation in several places

.. _#24: https://gitlab.com/ternaris/marv-robotics/issues/24
.. _#26: https://gitlab.com/ternaris/marv-robotics/issues/26
.. _#27: https://gitlab.com/ternaris/marv-robotics/issues/27
.. _#28: https://gitlab.com/ternaris/marv-robotics/issues/28


.. _v18_02:

18.02 (2018-02-05)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Support bag sets without timestamp in filenames `#16`_
- Support running selected nodes for all collections
- Support listing of and force running dependent nodes
- Support loading of custom.css and custom frontend files

Changed
~~~~~~~
- Preliminary support for topics with mixed message types `#21`_
- Speedup rendering in frontend
- Colorize point clouds
- Take message type definitions from bag files (needs migration, see :ref:`migrate_17_11_to_18_02`)

Fixed
~~~~~
- Fix sexpr for getting node without dot qualifier
- Fix filtering for datetime fields
- Fix loading of cloned persistent nodes
- Handle empty bag files
- Log error messages instead of several exceptions

.. _#16: https://gitlab.com/ternaris/marv-robotics/issues/16
.. _#21: https://gitlab.com/ternaris/marv-robotics/issues/21


.. _v17_11:

17.11 (2017-11-17)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Document MARV Robotics nodes
- Document configuration directives
- Document HTTP API
- Document migration from Community Edition 16.10
- Support import of datasets from Community Edition 16.10
- Co-release 17.11 community and enterprise edition

Changed
~~~~~~~
- Improve s-expression functions for configuration file
- Switch to flat store (needs migration, see :ref:`migrate_16_10_to_17_11`)


.. _v17_08:

17.08 (2017-08-23)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Custom widget support
- OAuth support
- Improve documentation for scanners
- Improve documentation for frontend widgets
- Video widget improvements
- Support more image formats
- Support system-wide configuration
- Improve cli error handling and logging

Fixed
~~~~~
- Frontend bug and styling fixes


.. _v17_06:

17.06 (2017-06-16)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Allow concurrent execution of multiple node run processes
- Admin panel for user and group management

Changed
~~~~~~~
- Make node syntax clearer to improve the node authoring experience
- Human readable pathnames in store
- Improve dataset query via command line
- Improve CLI logging
- Advanced access control
- Improve point cloud handling

Fixed
~~~~~
- Improve tag cloud styling with a responsive design
- Keep frontend state and scroll positions between page refreshes
- Speed up loading of large collections
- Render multi colored trajectories with markers correctly


.. _v17_05:

17.05 (2017-05-05)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Implement generator based node concurrency
- Optionally spawn node instances per topic or message type
- Allow collections to define an arbitrary number of scanroots `#4`_
- Improve performance with reduced JavaScript footprint
- Improve node runner and introduce basic query cli
- Add configurable compare view to display data of multiple datasets
- Add graphical live filters to listing page
- Make summary section of detail view customizable
- Display time added column
- Support most of rosbag play switches in marv ros play

Changed
~~~~~~~
- Store data in an efficient binary format
- Use schemas to enforce data integrity
- Manage multiple collections of different datasets
- Configure detail views in Python nodes
- Replace Python code in config file with simpler expressions
- Redesign map widget, support trajectory animations
- Stream huge datasets to point cloud widget
- Improve mass tagging performance
- Improve listing update performance

.. _#4: https://gitlab.com/ternaris/marv-robotics/issues/4


.. _v16_10:

16.10 (2016-10-07)
^^^^^^^^^^^^^^^^^^

- Initial release
