.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _config:

Configuration
=============

The configuration file ``marv.conf`` is in Python config parser / ini-syntax and consists of at least one :ref:`cfg_section_marv` and one or more :ref:`cfg_section_collection`. See some :ref:`cfg_examples` below.

If you make changes to your configuration, keep in mind that you have to stop ``gunicorn``, run ``marv init``, and start ``gunicorn`` again.


Relative paths
--------------
The location of ``marv.conf`` is the site directory and relative paths are relative to that directory.


.. _cfg_section_marv:

marv section
------------
.. code-block:: ini

   [marv]


.. _cfg_marv_acl:

acl
^^^
Use access control lists to control who can perform which actions. See :mod:`marv_webapi.acls` for more information.

Example:

.. code-block:: ini

   acl = marv_webapi.acls:public

Default:

.. code-block:: ini

   acl = marv_webapi.acls:authenticated


.. _cfg_marv_collections:

collections
^^^^^^^^^^^
Name of one or more collections, corresponding to a :ref:`cfg_section_collection`.

Example:

.. code-block:: ini

   collections = bags


.. _cfg_marv_dburi:

dburi
^^^^^
Location of sqlite database. Despite the generic name, only sqlite is supported.

Example:

.. code-block:: ini

   dburi = sqlite:////var/local/lib/marv/db/db.sqlite

Default:

.. code-block:: ini

   dburi = sqlite:///path/to/sitedir/db/db.sqlite

.. note::

   Keep the ``db/db.sqlite`` suffix for ease of migrations.


.. _cfg_marv_reverse_proxy:

reverse_proxy
^^^^^^^^^^^^^
When marv is running behind a reverse proxy, serving of files can be offloaded for greatly improved performance. Currently, the only supported reverse proxy is ``nginx``.

Example:

.. code-block:: ini

   reverse_proxy = nginx

See :ref:`deploy_nginx` for the corresponding nginx configuration.


.. _cfg_marv_store:

storedir
^^^^^^^^
Example:

.. code-block:: ini

   storedir = /var/local/lib/marv/store

Default:

.. code-block:: ini

   storedir = ./store


.. _cfg_upload_checkpoint_commands:

upload_checkpoint_commands
^^^^^^^^^^^^^^^^^^^^^^^^^^
List of commands that is executed before marv touches a collection's scanroot as part of an upload from a leaf. See :ref:`upload` for more information.

Example:

.. code-block:: ini

   upload_checkpoint_commands =
       /path/to/checkpoint/script

Content of checkpoint script:

.. code-block:: sh

   #!/bin/sh

   NAME="$(basename "${MARV_SCANROOT}")"
   sudo btrfs subvolume snapshot -r "${MARV_SCANROOT}" /snapshots/"${NAME}"-$(date -u '+%Y-%m-%dT%H:%M:%SZ')

Checkpoint script needs to be executable (``chmod +x``) and user running marv needs to have sudoer permission for btrfs:

.. code-block::

   marvuser ALL=(root) /usr/bin/btrfs subvolume snapshot -r /path/to/scanroot /snapshots/*


.. _cfg_section_collection:

collection section
------------------
Configuration for a collection of datasets.


.. _cfg_c_scanner:

scanner
^^^^^^^
A scanner is responsible to group files into named datasets.

Example:

.. code-block:: ini

   scanner = marv_robotics.bag:scan

See :func:`marv_robotics.bag.scan`


.. _cfg_c_scanroots:

scanroots
^^^^^^^^^
One or more directories to scan for datasets.

Example:

.. code-block:: ini

   scanroots =
       ./foo
       ./bar

.. warning::

   MARV Robotics does not need write access to your bag files. As a safety measure install and run MARV as a user having only read-only access to your bag files.


.. _cfg_c_nodes:

nodes
^^^^^
List of nodes made available within this collection under the name following the column, which is also the name of the function the node is created from. When listing colums or filters are added, the given extractor function run for all the collection's datasets. For this to be quick, all node output used in listing colums and filters must be readily available. Therefore all nodes listed in the configuration are persisted in the store. For a node to be persisted it needs to define a message schema. See :ref:`tutorial_declare_image_node` for an example.

Example:

.. code-block:: ini

   nodes =
       # pkg.module:func_name
       marv_nodes:dataset
       marv_robotics.bag:bagmeta

For a list of nodes see :ref:`nodes`.


.. _cfg_c_filters:

filters
^^^^^^^
Listings of datasets for the web frontend and API responses can be filtered.

Nodes extract and process data from datasets. Node output persisted in the store is available via a node's name. For this to happen the node needs to define a message type and be listed in :ref:`cfg_c_nodes`. Filters and :ref:`cfg_c_listing_columns` use :ref:`cfg_sexp` to extract values from node output. Via API or web frontend a user supplies filter input to be compared with the extracted value using a selected operator. A filter's name is displayed in the web frontend and its ID is used via API.

At least one operator has to be configured per filter and valid operators depend on the field type. The ``tags`` and ``comments`` filter are special and have to be defined exactly as shown below.

See :ref:`cfg_sexp` on how to create functions to extract values from node output.

Example:

.. code-block:: ini

   filters =
       # id     | Display Name | operators         | field type | extractor function
       name     | Name         | substring         | string     | (get "dataset.name")
       setid    | Set Id       | startswith        | string     | (get "dataset.id")
       size     | Size         | lt le eq ne ge gt | filesize   | (sum (get "dataset.files[:].size"))
       tags     | Tags         | any all           | subset     | (tags )
       comments | Comments     | substring         | string     | (comments )
       fulltext | Fulltext     | words             | words      | (get "fulltext.words")
       files    | File paths   | substring_any     | string[]   | (get "dataset.files[:].path")
       end_time | End time     | lt le eq ne ge gt | datetime   | (get "bagmeta.end_time")
       duration | Duration     | lt le eq ne ge gt | timedelta  | (get "bagmeta.duration")
       topics   | Topics       | any all           | subset     | (get "bagmeta.topics[:].name")

In case you use emacs, it's easy to align these: ``C-u M-x align-regexp | RET RET y``.


field type
~~~~~~~~~~
The field type determines what python type the extractor function is expected to return, how this is interpreted and displayed, and what is expected as filter input.

``datetime``
''''''''''''
| extract: int, nanoseconds since epoch
| input: int, millisecons since epoch
| operators: ``lt`` ``le`` ``eq`` ``ne`` ``ge`` ``gt``

``filesize``
''''''''''''
| extract: int, bytes
| input: int, bytes
| operators: ``lt`` ``le`` ``eq`` ``ne`` ``ge`` ``gt``

``float``
''''''''''''
| extract: float
| input: float
| operators: ``lt`` ``le`` ``eq`` ``ne`` ``ge`` ``gt``

``int``
''''''''''''
| extract: int
| input: int
| operators: ``lt`` ``le`` ``eq`` ``ne`` ``ge`` ``gt``

``string``
''''''''''
| extract: unicode
| input: utf-8
| operators: ``substring``, ``startswith``

``string[]``
''''''''''''
| extract: list of unicode
| input: utf-8
| operators: ``substring_any``

``subset``
''''''''''
| extract: list of unicode
| input: list of utf-8
| operators: ``any``, ``all``

``timedelta``
'''''''''''''
| extract: int, nanoseconds
| input: int, millisecons
| operators: ``lt`` ``le`` ``eq`` ``ne`` ``ge`` ``gt``

``words``
'''''''''
| extract: list of unicode
| input: list of utf-8
| operators: ``words``


operators
~~~~~~~~~

``lt`` ``le`` ``eq`` ``ne`` ``ge`` ``gt``
'''''''''''''''''''''''''''''''''''''''''
Comparison of numeric input with numeric stored value.


``substring``
'''''''''''''
Match input as substring anywhere in stored string.


``startswith``
''''''''''''''
Stored string starts with input string.


``substring_any``
'''''''''''''''''
The input string is a substring of any string in a stored list of strings.


``any``
'''''''
The set of input strings intersects with the set of stored strings.


``all``
'''''''
The set of input strings is a subset of the set of stored strings.


.. _cfg_c_listing_columns:

listing_columns
^^^^^^^^^^^^^^^
Columns displayed for the collection's listing.

For certain colums the id is important, so keep the ids used in the :ref:`cfg_default_config`. The heading is used as column heading, formatters are explained below and see :ref:`cfg_sexp` on how to write functions to extract values from node output.

Example:

.. code-block:: ini

   listing_columns =
       # id | Heading | formatter | extractor function
       name | Name    | route     | (detail_route (get "dataset.id") (get "dataset.name"))
       size | Size    | filesize  | (sum (get "dataset.files[:].size"))


.. _cfg_c_formatter:

formatter
~~~~~~~~~
Marv ships with a set of formatters. See :ref:`widget_custom` on how to override these and supply your own.


``acceleration``
''''''''''''''''
Renders numeric value with unit. Unit can be chosen in frontend (EE).

| extract: float (m/s^2)

``date``
''''''''
| extract: int, nanoseconds since epoch

``datetime``
''''''''''''
| extract: int, nanoseconds since epoch

``distance``
''''''''''''
Renders numeric value with unit. Unit can be chosen in frontend (EE).

| extract: float (m)

``float``
'''''''''
Renders float with two decimal places.

| extract: float

``icon``
''''''''
Render a `glyphicon <https://getbootstrap.com/docs/3.3/components/#glyphicons>`_ by name (``glyphicon-<name>``) with optional additional space-separated css classes and a title rendered in a tooltip for the icon.

| extract: ``{'icon': name, 'classes': css_classes, 'title': title}``

``int``
'''''''
| extract: int

``link``
''''''''
| extract: ``{'href': '', 'title': ''}``

``pill``
''''''''
| extract: int, float, unicode

``route``
'''''''''
Used only for the detail route so far in conjunction with :ref:`cfg_sexp_detail_route`.

``speed``
'''''''''
Renders numeric value with unit. Unit can be chosen in frontend (EE).

| extract: float (m/s)

``string``
''''''''''
| extract: int, float, unicode

``timedelta``
'''''''''''''
| extract: int, nanoseconds since epoch


.. _cfg_c_listing_sort:

listing_sort
^^^^^^^^^^^^
Column and sort order for listing.

Example:

.. code-block:: ini

   listing_sort = start_time | descending

The first field corresponds to an id in :ref:`cfg_c_listing_columns`, the second is one of ``ascending`` (default) or ``descending``.


.. _cfg_c_listing_summary:

listing_summary
^^^^^^^^^^^^^^^
Summary calculated for the filtered rows of the listing.

Example:

.. code-block:: ini

   listing_summary =
       # id     | Title    | formatter | extractor
       datasets | datasets | int       | (len (rows))
       size     | size     | filesize  | (sum (rows "size" 0))
       duration | duration | timedelta | (sum (rows "duration" 0))

A unique id, a title displayed below the value, a formatter explained in :ref:`cfg_c_formatter` and extractor function explained in :ref:`cfg_sexp`.


.. _cfg_c_detail_summary_widgets:

detail_summary_widgets
^^^^^^^^^^^^^^^^^^^^^^
List of widgets to be rendered on the first tab of the detail view, aka the summary section.

Example:

.. code-block:: ini

   detail_summary_widgets =
       summary_keyval
       bagmeta_table

You can write your own and use some of the already existing :ref:`widget_nodes`.

.. _cfg_c_detail_sections:

detail_sections
^^^^^^^^^^^^^^^
List of detail section to be rendered beyond the summary section. For any given dataset those sections will be rendered only if the dataset contains the necessary data. In absence of meaningful data, sections will be omitted from the web frontend detail view.

Example:

.. code-block:: ini

   detail_sections =
       connections_section
       video_section

You can write your own and use some of the already existing :ref:`section_nodes`.


.. _cfg_sexp:

S-Expressions
-------------
S-Expressions are used in the config file to create small functions that extract values from output of stored :ref:`cfg_c_nodes`. S-Expressions are (nested) lists in parentheses, with list elements being separated by spaces.

.. code-block:: lisp

   (get "dataset.name")
   (get "dataset.files[:].path")
   (sum (get "dataset.files[:].size"))
   (tags)
   (comments)

The first element of a list is the name of a function. Any additional arguments are passed as arguments to the function and the list defining a function is replaced with its return value.

Valid arguments are:

- functions enclosed in ``()``
- all json literals
  - ``null``
  - ``true``, ``false``
  - integers ``-17``, ``42``, ...
  - floats ``1.2``, ``-1e10``
  - ``"strings with escape sequences \u0022 \" \\ \b \f \n \r \t"``


Functions
^^^^^^^^^
Functions in S-expressions get and process data from store node output. Some may be used in all scopes :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`, and :ref:`cfg_c_listing_summary`; some only in some (see below).


``comments``
~~~~~~~~~~~~
Return list of unicode objects with text of comments.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


.. _cfg_sexp_detail_route:

``detail_route``
~~~~~~~~~~~~~~~~
Return dictionary rendering link to detail route of dataset. First argument is the dataset's setid, second optional name is displayed instead of setid.

scope: :ref:`cfg_c_listing_columns`


``filter``
~~~~~~~~~~
Filter list by removing ``null`` elements (Python ``None``).

Examples:

.. code-block:: lisp

   (filter null (makelist (get "unit.name")))

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``format``
~~~~~~~~~~
Wrapper for ``fmt.format(*args)``. First argument is the format string ``fmt``, remaining arguments are passed on.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``get``
~~~~~~~
Get a value from a nodes output. First argument defines node and traversal into its output, second optional argument is used as default value instead of ``None``.

Examples:

.. code-block:: lisp

   (get "bagmeta.start_time")
   (get "dataset.files[:].size")

The specifier starts with the nodes name. A ``.`` performs dictionary key lookup. Lists can be traversed into in part or full using slicing and further dictionary lookup is performed on each element of the list.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``getitem``
~~~~~~~~~~~
Get an item from a list or dictionary.

.. code-block:: lisp

   (getitem (split (get "foo.bar") "/" 1) 0)

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``join``
~~~~~~~~
Wrapper for ``joinstr.join(args)``. First argument is the join string remaining arguments are joined with.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``len``
~~~~~~~
Return length of first argument.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`, :ref:`cfg_c_listing_summary`


``link``
~~~~~~~~
Render link with first argument as href and second argument displayed.

scope: :ref:`cfg_c_listing_columns`


``makelist``
~~~~~~~~~~~~
Takes one or more arguments and returns a list containing these.

Examples:

.. code-block:: lisp

   (filter null (makelist (get "unit.name")))

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``max``
~~~~~~~
Return maximum element of first argument.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`, :ref:`cfg_c_listing_summary`


``min``
~~~~~~~
Return minimum element of first argument.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`, :ref:`cfg_c_listing_summary`


``rows``
~~~~~~~~
Return all rows matching current filter criteria. The optional second and third arguments extracts a specific column defined in :ref:`cfg_c_listing_columns` instead of the full row and provide a default value for it.

Examples:

.. code-block:: lisp

   (sum (rows "size" 0))

scope: :ref:`cfg_c_listing_summary`


``rsplit``
~~~~~~~~~~
Split string from the right. First argument is the string, further arguments are passed to python's string rsplit method.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``set``
~~~~~~~
Return set with items from one iterable argument.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`, :ref:`cfg_c_listing_summary`


``split``
~~~~~~~~~
Split string. First argument is the string, further arguments are passed to python's string split method.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``sum``
~~~~~~~
Return sum of arguments.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`, :ref:`cfg_c_listing_summary`


``tags``
~~~~~~~~
Return list of tags associated with dataset.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


``trace``
~~~~~~~~~
Print trace messages.

scope: :ref:`cfg_c_filters`, :ref:`cfg_c_listing_columns`


.. _cfg_examples:

Examples
--------


.. _cfg_default_config:

Default configuration
^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: config/marv.conf


System-wide configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

``/etc/marv/marv.conf``

.. literalinclude:: config/etc_marv_marv.conf


Multiple collections
^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: config/marv_multiple.conf
