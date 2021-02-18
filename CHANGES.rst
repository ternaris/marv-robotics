.. _changelog:

Changelog
---------

Our versioning scheme uses a two-digit year, a two-digit month, and a release counter within month. Previously the release counter was omitted when zero.

Changes necessitating migration reference the corresponding migration section. References are only rendered correctly as part of the Sphinx documentation. Within GitLab please find the migration document `here <./docs/migrate/index.rst>`_.

If we're deprecating features you rely on, please speak up.


.. _v20.12.0:

20.12.0 (2021-02-18)
^^^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Plotly widget `#37`_
- Tests for image format conversions
- Support for sensor_msgs/CompressedImage in cam nodes `#78`_
- Warnings if rosbag2 contains subdirectories or files not listed in metadata.yaml
- Directory-based scanner as alternative to the default rosbag record set-based scanner
- Pure-python rosbag2 reader
- Log warning message from node Abort exception
- New collection query API `#82`_ **needs migration:** :ref:`migrate-20.12.0`
- Formatters for distance, speed, and acceleration
- Nodes extracting basic motion parameters
- Support for nested listing summary functions
- Added filter config function
- Added makelist config function
- Fallback to bag message timestamp in case ROS message header timestamp is zero
- CLI version option to display version and copyright information
- API call to get path to site resource within node (marv.get_resource_path())
- Support to publish frontend updates independent of full releases (CE)
- Let CI run pytest for community edition merge requests (CE)
- Let CI publish latest documentation as gitlab pages (CE)
- PDF widget (EE)
- PDF section to display PDF files contained in dataset (EE)
- Support finding and reading metadata of rosbag2 datasets (EE); CE got support in :ref:`v20.08.0` already
- Support reading and deserializing of rosbag2 datasets (EE); CE got support in :ref:`v20.08.0` already
- Extraction and visualization of autonomous distance driven (EE)
- Support for DMV reporting workflows (EE)
- Render markers in pointcloud player (EE)
- Render ego model and static pointcloud/vector maps in pointcloud views (EE)

Changed
~~~~~~~
- Replace custom rosbag merge sort with heapq.merge `#72`_
- Use heapq.merge to read from multiple bags in parallel `#72`_
- Serve documentation from marv core
- Switch to isort for import order management
- Deprecated module attributes are not displayed in module __dir__ anymore
- Prepare to run nodes in dedicated environment with marv-api and marv-robotics nodes
- Use pydantic to model configuration
- Validate node output on marv.push() to allow debugging of schema violations in node context
- Check that @marv.node() decorator is called before being applied
- Changed ffmpeg parameters to improve web streaming
- Require Python 3.8 for new language features; if you need support for Python 3.7 please let us know
- Check not to overwrite existing dump file
- Tagging via CLI to be idempotent by default, previously it failed when trying to add existing or remove non-existing tags
- Disabled fulltext node in default config as it can lead to excessive DB memory usage; enable selectively instead
- Publish marv_robotics.trajectory.navsatfix timestamps in nanoseonds **needs migration:** :ref:`migrate-20.12.0` for custom nodes directly consuming the navsatfix node
- Updated python dependencies
- Silence aiosqlite exception logging, among others when trying to add users or groups that exist already
- Remove remaining EE-only leaf database model from (CE)
- Switch CE docker image base to plain Ubuntu focal as we don't have any external ROS dependencies anymore (CE)
- Move widget dropdown to CE, previously EE only (CE)
- Move widget mpld3 to CE, previously EE only (CE)
- Ship frontend as part of marv python distribution (CE)
- Publish latest tag as latest image to dockerhub and do not publish image for master branch (CE)
- Introduce dedicated connections section for partial downloads (EE) **needs migration:** :ref:`migrate-20.12.0`

Deprecated
~~~~~~~~~~
- 21.04 will remove marv.types, use marv_api.types instead
- 21.04 will remove marv.utils.popen, use marv_api.utils.popen instead
- 21.04 will remove the deprecated HTTP listing API, query :ref:`httpapi_query_collection` instead
- 21.04 will remove list config function, use makelist instead

Removed
~~~~~~~
- Previously deprecated marv.api_endpoint and marv.api_group, deprecated in :ref:`v20.04.0`
- All marv.* controls, available via marv_api since :ref:`v20.04.0`
- Support to install via pypi; use ./scripts/setup-venv instead
- rosbag2_py from CE docker image in favor of pure-python rosbag2 contained in marv-robotics

Fixed
~~~~~
- Conversion of YUV422 encoded images
- Return HTTP bad request from query API on unknown filter names `#83`_
- Pass user argument to database method from marv show cli command `#87`_
- Enabled cloned nodes as input for cloning
- Prevent worker from restarting in case of errors during marv serve startup
- Let len, min, max, and sum config functions handle None values
- Sexp for detail_title may now take multiple arguments
- Running nodes referenced by dotted name
- Yielding marv file objects via marv.push() in addition to plain yielding
- Listing batch processing during re-initialisation of site
- Sort connection indices in external rosbag module to align with rosbag play `#72`_
- Fulltext node treats null characters as whitespace instead of passing them on and producing an invalid SQL query
- Sorting of incomplete listing columns that prevented rendering in some cases `#88`_
- Gracefully handle unindexed rosbag1 files `#88`_
- Config error exception handling
- Authentication using OAuth2 webflow in Firefox (EE)

.. _#37: https://gitlab.com/ternaris/marv-robotics/issues/37
.. _#72: https://gitlab.com/ternaris/marv-robotics/issues/72
.. _#78: https://gitlab.com/ternaris/marv-robotics/issues/78
.. _#82: https://gitlab.com/ternaris/marv-robotics/issues/82
.. _#83: https://gitlab.com/ternaris/marv-robotics/issues/83
.. _#87: https://gitlab.com/ternaris/marv-robotics/issues/87
.. _#88: https://gitlab.com/ternaris/marv-robotics/issues/88


.. _v20.08.0:

20.08.0 (2020-08-09)
^^^^^^^^^^^^^^^^^^^^

**This release contains security fixes. We strongly recommend that all affected MARV installations be upgraded immediately and migration instructions be followed.**

Added
~~~~~
- Automatically install custom python packages in site/code (CE)
- Bagmeta_table supports datasets with bags and non-bag files
- Support passing nodes to clone without wrapping with marv.select
- Make DAG nodes hashable to use them as dictionary keys and to create sets of them
- Support selecting multiple topics and message types by comma-separated selectors
- Add support for finding and reading rosbag2 datasets (CE)
- GNSS, fulltext and trajectory nodes also process rosbag2 datasets (CE)

Changed
~~~~~~~
- Improve formatting of null values in listing and table widget
- Use docker entry point from checkout without rebuilding image
- Support all json literals in config file s-expressions and relax whitespace handling
- Update all python dependencies
- Cleanup home directory cache in docker images (CE)
- Switch to Python 3.8 while keeping support for Python 3.7
- Create marv user upon startup with uid and gid of user starting it; remove the need to rebuild image to that end (CE)

Fixed
~~~~~
- Sort order of table columns containing links **needs migration:** :ref:`migrate-20.08.0`
- Execution of run-container from outside repository root
- Pushing of false values and values with ambiguous truth
- Running dependent nodes by marv run --force-dependent
- Adjusting marv run cache size via the --cachesize option
- Edge case where nodes would run out-of-sync and requesting messages were not available anymore
- Properly handle SIGINT and SIGTERM during marv run

Security
~~~~~~~~
- Tighten file permissions for session key file, was readable for all users on host system **needs migration:** :ref:`migrate-20.08.0`
- Update Pillow for `CVE-2020-10177`_, `CVE-2020-10379`_, `CVE-2020-10994`_, `CVE-2020-11538`_

.. _CVE-2020-10177: https://nvd.nist.gov/vuln/detail/CVE-2020-10177
.. _CVE-2020-10379: https://nvd.nist.gov/vuln/detail/CVE-2020-10379
.. _CVE-2020-10994: https://nvd.nist.gov/vuln/detail/CVE-2020-10994
.. _CVE-2020-11538: https://nvd.nist.gov/vuln/detail/CVE-2020-11538


.. _v20.06.0:

20.06.0 (2020-06-29)
^^^^^^^^^^^^^^^^^^^^

Added
~~~~~
- System user for unauthenticated requests
- System groups for all unauthenticated users
- Granular access control for collections and datasets (EE)
- HTTP API to trigger scans and node runs (EE)
- Support split bags without prefix
- Dropdown container widget (EE)
- Database version checks on marv startup

Changed
~~~~~~~
- Streamline action verbs supported by access control profiles, **needs migration:** :ref:`migrate-20.06.0`
- Collections are reflected in the database schemas, **needs migration:** :ref:`migrate-20.06.0`
- Publish permissions on a granular per resource basis
- Improve test coverage of web APIs for site administration
- Improve testing fixtures and general test coverage
- Update mpld3 version (EE)

Fixed
~~~~~
- Fix embedding of custom.js and custom.css
- Handling of changed file mtimes in marv scan `#77`_
- Handle exceptions for cli commands with uninitialised site
- Styling for table action responses
- Download permissions for dataset files; erroneously no access was given (EE)

.. _#77: https://gitlab.com/ternaris/marv-robotics/issues/77


.. _v20.04.0:

20.04.0 (2020-04-30)
^^^^^^^^^^^^^^^^^^^^

**This release contains important security fixes. We strongly recommend that all affected MARV installations be upgraded immediately.**

Security
~~~~~~~~

- Fix directory traversal bug that allowed arbitrary filesystem reads when running without nginx. The faulty code got introduced with :ref:`v19.09.0`. Earlier versions and setups using nginx are not affected.
- Upgrade tortoise-orm for `CVE-2020-11010`_

.. _CVE-2020-11010: https://nvd.nist.gov/vuln/detail/CVE-2020-11010

Added
~~~~~
- Support uninstall of python packages in single binary mode (EE)
- Support for leaves to upload datasets (EE)
- Add infrastructure to manage deprecations warnings
- Introduce marv_api package to bundle public API for node development

Changed
~~~~~~~
- Update python dependencies and tooling
- Update to most recent tortoise-orm, **needs migration:** :ref:`migrate-20.04.0`
- Improved map layer controls
- Prepare for asynchronous node execution in multiple processes
- Simplify node testing by introducing a wrapper for run_nodes
- Start moving code from marv into newly introduced marv_api
- Use DAG based on pydantic models to represent node graph
- Change marv serve to bind per default only to localhost for development
- State clearly that gunicorn without nginx as reverse-proxy is only meant for development

Deprecated
~~~~~~~~~~
- In 20.07, marv.api_endpoint and marv.api_group will be removed, please let us know if you need these
- All marv.* controls are now available via marv_api and will be removed from old location in 20.07

Removed
~~~~~~~
- Unittest dependency of node testing base class
- Unused and long deprecated code
- Support for shortened setids on CLI
- Internally used marv.fork and marv.get_stream controls

Fixed
~~~~~
- Fix color conversion for bayer mask images
- Fix marv discard argument parsing
- Fix queries for outdated datasets
- Fix documentation for widget pre
- Fix pip dist-info discovery for packages contained in bundle (EE)
- Fix position of CLI config option in docs
- Fix time-wise sorting of messages from different bags
- Run ffmpeg in sanitized environment to prevent exec errors in single binary mode (EE)
- Load marv pip managed user site only when running from pyinstaller bundle (EE)
- Remove distutils trove classifiers that are not applicable anymore
- Warning when building documentation
- Do not reset map zoom on window resize `#67`_
- Properly shutdown node and driver generators upon driver restart
- Support passing parameters to marv serve in docker setup `#74`_
- Properly close stream file handles before cleaning up temporary directories `#75`_

.. _#67: https://gitlab.com/ternaris/marv-robotics/issues/67
.. _#74: https://gitlab.com/ternaris/marv-robotics/issues/74
.. _#75: https://gitlab.com/ternaris/marv-robotics/issues/75


.. _v19.11.1:

19.11.1 (2019-12-13)
^^^^^^^^^^^^^^^^^^^^

Fixed
~~~~~
- Let marv pip install understand what packages are contained within bundle (EE)
- Let marv python see marv pip installed packages (EE)


.. _v19.11.0:

19.11.0 (2019-12-01)
^^^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Add query API
- Add single binary installation method (EE)

Changed
~~~~~~~
- Provide marv serve cli to replace gunicorn, **needs migration:** :ref:`migrate-19.11.0`
- Speedup database queries
- Switch from sqlalchemy to tortoise-orm, **needs migration:** :ref:`migrate-19.11.0`
- Remove need for four slashes for absolute database URI `#68`_
- Contribution guide to require contributions to documentation be licensed under CC-BY-4.0 instead of CC-BY-SA-4.0
- Upgrade python gnupg library and silence log message upon import
- Make opencv an optional dependency

Removed
~~~~~~~
- Remove unneeded dependencies
- Drop support for ancient rosbag formats
- Drop support to reference multiple datasets by common prefix

Fixed
~~~~~
- Support non-ascii characters in API filters `#70`_
- Use correct timestamp to playback messages from multiple bags `#72`_
- Explicitly set algorithm for json web tokens

.. _#68: https://gitlab.com/ternaris/marv-robotics/issues/68
.. _#70: https://gitlab.com/ternaris/marv-robotics/issues/70
.. _#72: https://gitlab.com/ternaris/marv-robotics/issues/72

.. _v19.09.0:

19.09.0 (2019-09-09)
^^^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Add linter and editorconfig
- Add marv_ros Python package as new home of ROS specific code
- Ship versions of genmsg, genpy, and rosbag to make MARV independent of a ROS installation
- Add support for sensor_msgs/CompressedImage `#60`_

Changed
~~~~~~~
- Include default matplotlibrc in marv-robotics Python distribution
- Replace cv_bridge with pure python conversions
- **BREAKING** Switch to Ubuntu Bionic base image without ROS but Python 3.7
- **BREAKING** Require Python 3.7
- Migrate code to Python 3.7
- Cleanup code according to linter feedback
- Ignore internal tables of newer sqlite versions for dump and restore
- Update Python requirements to latest versions
- Clean older changelog entries and add links to issues and MRs
- Speed up rendering and sorting of tables with large number of rows
- Drop flask-sqlalchemy in favour of plain sqlalchemy
- Switch from flask to aiohttp powered by gunicorn **needs migration:** :ref:`migrate-19.09.0`

Removed
~~~~~~~
- Remove unneeded dependencies

Fixed
~~~~~
- Fix out of range video encoding bug by using newer ffmpeg version (3.4.6) in docker image `#59`_
- Correct handling of 16 bit single channel image types `#29`_

Security
~~~~~~~~
- Rebuild images published on dockerhub for latest release and master branch by GitLab CI nightly if a newer base image is available

.. _#29: https://gitlab.com/ternaris/marv-robotics/issues/29
.. _#59: https://gitlab.com/ternaris/marv-robotics/issues/59
.. _#60: https://gitlab.com/ternaris/marv-robotics/issues/60

.. _v19.07.0:

19.07.0 (2019-07-14)
^^^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Add marv show cli command to show basic information about datasets `#62`_

Fixed
~~~~~
- Fix pycapnp wrapper to handle nested lists
- Fix broken CE docker image builds `#66`_
- Fix pasting into multi-select input field `#65`_
- Automatically cleanup node output from unsuccessful previous runs `#64`_
- Let gnss node gracefully handle bags without valid messages `!65`_
- Fix loading of raster tiles during window resize `#63`_

.. _#62: https://gitlab.com/ternaris/marv-robotics/issues/62
.. _#63: https://gitlab.com/ternaris/marv-robotics/issues/63
.. _#64: https://gitlab.com/ternaris/marv-robotics/issues/64
.. _#65: https://gitlab.com/ternaris/marv-robotics/issues/65
.. _#66: https://gitlab.com/ternaris/marv-robotics/issues/66
.. _!65: https://gitlab.com/ternaris/marv-robotics/merge_requests/65

.. _v19.04.0:

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
- Move to GitLab to consolidate tooling `#54`_
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
- Fix support for GeoJSON points in trajectory widget `#50`_
- Let trajectory node produce correct GeoJSON for segments with only one coordinate
- Fix filtering of date fields with greater than or equals operation
- Only display successfully converted videos in video detail section

Security
~~~~~~~~
- Upgrade pyyaml library for `CVE-2017-18342`_
- Upgrade requests library for `CVE-2018-18074`_

.. _#50: https://gitlab.com/ternaris/marv-robotics/issues/50
.. _#54: https://gitlab.com/ternaris/marv-robotics/issues/54
.. _#58: https://gitlab.com/ternaris/marv-robotics/issues/58
.. _CVE-2017-18342: https://nvd.nist.gov/vuln/detail/CVE-2017-18342
.. _CVE-2018-18074: https://nvd.nist.gov/vuln/detail/CVE-2018-18074


.. _v19.02.0:

19.02.0 (2019-02-09)
^^^^^^^^^^^^^^^^^^^^

Changed
~~~~~~~
- Improve frontend render performance
- Improve testing and deployment infrastructure
- Prepare migration to GitLab
- Unify versioning of frontend and Python packages
- Dropped ipdb in favour of pdbpp, **needs migration:** :ref:`migrate-19.02.0`

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


.. _v18.07:

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
- Support streams of individual topics as optional inputs `#25`_, **needs migration:** :ref:`migrate-18.07`

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


.. _v18.05.1:

18.05.1 (2018-05-11)
^^^^^^^^^^^^^^^^^^^^

Fixed
~~~~~
- Correct coordinate transformations for cached trajectories


.. _v18.05:

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


.. _v18.04:

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
- Installation methods have significantly changed, **reinstall is recommended:** :ref:`migrate-18.04`

Fixed
~~~~~
- Fix trajectory generation
- Fix erroneous self-referentiality of some capnp structs
- Fix color format for opencv bridge


.. _v18.03:

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
- Changed GeoJSON property object needs rerender, **needs migration:** :ref:`migrate-18.03`

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


.. _v18.02:

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
- Take message type definitions from bag files, **needs migration:** :ref:`migrate-18.02`

Fixed
~~~~~
- Fix sexpr for getting node without dot qualifier
- Fix filtering for datetime fields
- Fix loading of cloned persistent nodes
- Handle empty bag files
- Log error messages instead of several exceptions

.. _#16: https://gitlab.com/ternaris/marv-robotics/issues/16
.. _#21: https://gitlab.com/ternaris/marv-robotics/issues/21


.. _v17.11:

17.11 (2017-11-17)
^^^^^^^^^^^^^^^^^^

Added
~~~~~
- Document MARV Robotics nodes
- Document configuration directives
- Document HTTP API
- Document migration from Community Edition 16.10
- Support import of datasets from Community Edition 16.10
- Co-release 17.11 Community and Enterprise Edition

Changed
~~~~~~~
- Improve s-expression functions for configuration file
- Switch to flat store, **needs migration:** :ref:`migrate-17.11`


.. _v17.08:

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


.. _v17.06:

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


.. _v17.05:

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


.. _v16.10:

16.10 (2016-10-07)
^^^^^^^^^^^^^^^^^^

- Initial release
