Changelog
---------


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


16.10 (2016-10-07)
^^^^^^^^^^^^^^^^^^

- Initial release


