.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _httpapi:

HTTP API
========

The API used between frontend and backend currently serves also for integration with other services. We are aware that this is suboptimal and will provide a proper versioned API in one of the next releases. Meanwhile this works and migration will be minimal.

To work with the API on the command line it is handy to have `curl <https://curl.haxx.se/>`_ and `jq <https://stedolan.github.io/jq/>`_.

.. code-block:: bash

   sudo apt-get install curl jq

Set an environment variable for the API.

.. code-block:: bash

   export MARV_API=http://localhost:8000/marv/api


.. _httpapi_auth:

Auth
----

For some API calls you need to be authenticated, let's get a token, and set handy environment vars.

.. code-block:: bash

   echo -n "Enter username: "; read -s MARV_USER && echo && \
   echo -n "Enter password: "; read -s MARV_PASS && echo && \
   TOKEN=$(curl -s -X POST -H "Content-Type: application/json" \
     -d '{"username": "'$MARV_USER'", "password": "'$MARV_PASS'"}' \
     $MARV_API/auth | jq -r .access_token) && \
   echo $TOKEN


Listing
-------

MARV knows two kind of ids for dataset.

1. setid; a random 128 bit integer, base32 encoded without padding chars, e.g. ``h27zmwsdzcnmu6kqncwdhhvrva``
2. id; id of the dataset within the database, e.g. ``42``

While the set id is unique for all times and across sites, for many interactions it is more efficient to use the database id.

Fetch id of all datasets:

.. code-block:: bash

   curl $MARV_API/collection |jq '.listing.widget.data.rows[] | .id'


And likewise for setid:

.. code-block:: bash

   curl $MARV_API/collection |jq '.listing.widget.data.rows[] | .setid'


.. _httpapi_filter:

Filter
^^^^^^
.. code-block:: bash

   curl -G \
     --data-urlencode \
     'filter={"name": {"op": "substring", "val": "leica"}}' \
     $MARV_API/collection \
     |jq '.listing.widget.data.rows[] | .setid'

.. code-block:: bash

   curl -G \
     --data-urlencode \
     'filter={"tags": {"op": "all", "val": ["bar", "foo"]}}' \
     $MARV_API/collection \
     |jq '.listing.widget.data.rows[] | .setid'

.. code-block:: bash

   curl -G \
     --data-urlencode \
     'filter={"tags": {"op": "any", "val": ["bar", "foo"]}}' \
     $MARV_API/collection \
     |jq '.listing.widget.data.rows[] | .setid'


List of dataset files
---------------------

.. code-block:: bash

   curl -X POST \
        -H "Content-Type: application/json" \
        -d "[42]" \
        $MARV_API/file-list

output:

.. code-block:: python

   {
     "paths": [
       "/scanroot/scan_odom_map_test.bag",
     ],
     "urls": [
       "dataset/h27zmwsdzcnmu6kqncwdhhvrva/0",
     ]
   }


Download
--------

First file of dataset

.. code-block:: bash

   curl -OJ $MARV_API/dataset/h27zmwsdzcnmu6kqncwdhhvrva/0


Comment
-------

.. code-block:: bash

   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
	-d '{"42": {"add": ["comment 1", "comment 2"]}}' \
	$MARV_API/comment

output:

.. code-block:: python

   {}


Delete
------

.. code-block:: bash

   curl -X DELETE \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
	-d "[1,2]" \
	$MARV_API/dataset

output:

.. code-block:: python

   {}

Deletion is idempotent.


.. _httpapi_tag:

Tag
---

.. code-block:: bash

   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
	-d '{"bags": {"add": {"foo": [42]}, "remove": {"bar": [17,42]}}}' \
	$MARV_API/tag

.. code-block:: python

   {}

Tagging is idempotent, missing tags are created, unused tags are not automatically cleaned up (see :ref:`maintenance`).
