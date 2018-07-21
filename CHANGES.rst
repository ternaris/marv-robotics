.. _changelog:

Changelog
---------

.. _v18_07:

18.07 (2018-07-22)
^^^^^^^^^^^^^^^^^^

- [BUGFIX] Support streams of individual topics as optional inputs
- [BUGFIX] Allow fulltext node to be used while directly subscribing to topics of std_msgs/String
- [BUGFIX] Document the need for configured nodes to define a schema
- [BUGFIX] Document the need for setting stream headers
- [BUGFIX] Improve cli exception handling and error messages for certain edge cases
- [BUGFIX] Reset graphical tag filters on collection switch
- [BUGFIX] Fix utm conversion for gnss node
- [BUGFIX] Properly set and reset outdated state of datasets
- [BUGFIX] Consistently set cache control header to disable caching of all content
- Document pattern for reducing multiple streams
- Add cli command for database dump and restore
- Add controls to adjust pointcloud playback speed
- Support querying for datasets with missing files
- Support link widgets with download attribute
- Update python dependencies, most notably latest pycapnp


.. _v18_05_1:

18.05.1 (2018-05-11)
^^^^^^^^^^^^^^^^^^^^

- [BUGFIX] Correct coordinate transformations for cached trajectories


.. _v18_05:

18.05 (2018-05-08)
^^^^^^^^^^^^^^^^^^

- Enable loading dataset node output in comparison views
- Set default matplotlib backend to Agg, removing the need to set it manually
- Auto-initialise previously unintialised site upon start
- Set marv docker container timezone to host timezone
- Support setting marv uid and gid for docker installation
- [BUGFIX] Better support for colour formats
- [BUGFIX] Add scanroot to documentation deploy example for nginx
- [BUGFIX] Cleanup form submit handling
- [BUGFIX] Fix native installation method for community edition
- [BUGFIX] Fix loading of videos for community edition
- [BUGFIX] Gracefully handle permission denied upon initialisation


.. _v18_04:

18.04 (2018-04-30)
^^^^^^^^^^^^^^^^^^

- Add command-line group management to Community Edition
- Speed-up streaming of videos and point clouds with nginx reverse-proxy
- Improve point cloud player controls
- Support configuration of access control lists
- Improve trajectory player controls
- Make styling of widgets more consistent
- Switch from nosetest to pytest and cleanup requirements
- Drop Bootstrap v3 in favour of slim custom Bootstrap v4 derivate
- Add docker setup with example site
- Merge and cleanup individual repositories
- [BUGFIX] Fix trajectory generation
- [BUGFIX] Fix erroneous self-referentiality of some capnp structs
- [BUGFIX] Fix color format for opencv bridge


.. _v18_03:

18.03 (2018-03-10)
^^^^^^^^^^^^^^^^^^

- Add more flexible GeoJSON properies to map widget
- Make marker geometry configurable on map widget
- Draw markers using last known heading on map in absence of explicit rotation values
- Document creation of custom capnp types
- Ship capnp types for atomic values and timed values
- Add, list and remove comments via command-line
- [BUGFIX] Display correct tags when paging in listing
- [BUGFIX] Render GeoJSON lines with correct width in Firefox
- [BUGFIX] Fix command-line tagging
- [BUGFIX] Gnss node handles absence of valid gps messages
- [BUGFIX] Add missing int and float formatters
- [BUGFIX] Validate names for newly added users and groups
- [BUGFIX] Document disabling of uwsgi buffering to enable downloads larger than 1GB
- [BUGFIX] Fix tags displayed in listing table for any but the first page
- [BUGFIX] Fix documentation in several places


.. _v18_02:

18.02 (2018-02-05)
^^^^^^^^^^^^^^^^^^

- Preliminary support for topics with mixed message types (needs migration)
- Support bag sets without timestamp in filenames
- Speedup rendering in frontend
- Colorize point clouds
- Support running selected nodes for all collections
- Support listing of and force running dependent nodes
- Support loading of custom.css and custom frontend files
- [BUGFIX] Fix sexpr for getting node without dot qualifier
- [BUGFIX] Fix filtering for datetime fields
- [BUGFIX] Fix loading of cloned persistent nodes
- [BUGFIX] Use message definitions from bag file instead of installed (needs migration)
- [BUGFIX] Handle empty bag files
- [BUGFIX] Log error messages instead of several exceptions


.. _v17_11:

17.11 (2017-11-17)
^^^^^^^^^^^^^^^^^^

- Improve s-expression functions for configuration file
- Switch to flat store (needs migration)
- Document marv robotics nodes
- Document configuration directives
- Document HTTP API
- Document migration from community edition 16.10
- Support import of datasets from community edition 16.10
- Corelease 17.11 community and enterprise edition


.. _v17_08:

17.08 (2017-08-23)
^^^^^^^^^^^^^^^^^^

- Custom widget support
- OAuth support
- Improve documentation for marv scanner
- Improve documentation for frontend widgets
- [BUGFIX] Frontend bug and styling fixes
- Video widget improvements
- Support more image formats
- Support system-wide configuration
- Improve cli error handling and logging


.. _v17_06:

17.06 (2017-06-16)
^^^^^^^^^^^^^^^^^^

- Make marv node syntax clearer to improve the node authoring experince
- Allow concurrent execution of multiple marv node run processes
- Human readable pathnames in store
- Improve datset query via command line
- Improve CLI logging
- Advanced access control
- Admin panel for user and group management
- Improve point cloud handling
- [BUGFIX] Improve tag cloud styling with a responsive design
- [BUGFIX] Keep frontend state and scroll positions between page refreshs
- [BUGFIX] Speed up loading of large collections
- [BUGFIX] Render multi colored trajectories with markers correctly


.. _v17_05:

17.05 (2017-05-05)
^^^^^^^^^^^^^^^^^^

- Store data in an efficient binary format
- Use schemas to enforce data integrity
- Implement generator based node concurrency
- Optionally spawn node instances per topic or message type
- Manage multiple collections of different datasets
- Allow collections to define an arbitrary number of scanroots
- Configure detail views in python nodes
- Replace python code in config file with simpler expressions
- Make summary section of detail view customizable
- Add configurable compare view to display data of multiple datasets
- Improve node runner and introduce basic query cli
- Improve performance with reduced javascript footprint
- Add graphical live filters to listing page
- Display time added column
- Redesign map widget, support trajectory animations
- Stream huge datasets to pointcloud widget
- Support most of rosbag play switches in marv ros play
- [BUGFIX] Improve mass tagging performance
- [BUGFIX] Improve listing update performance


.. _v16_10:

16.10 (2016-10-07)
^^^^^^^^^^^^^^^^^^

- Initial release


