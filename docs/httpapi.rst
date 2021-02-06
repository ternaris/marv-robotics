.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _httpapi:

HTTP API
========

MARV provides an HTTP API for integration with other services. There is a dedicated API endpoint that can be used to run complex queries on the MARV database. For performing actions like tagging or commenting there are no dedicated endpoints at this time, and we recommend using the frontend API endpoints documented below for the time being.

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


.. _httpapi_query:

Query
-----

Database queries can be performed by posting a corresponding request to ``v1/rpcs``. The endpoint expects a json encoded object with an ``rpcs`` key and a list of actions to run. An empty request and its response would look like:

.. code-block:: bash

   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"rpcs": []}' \
        $MARV_API/v1/rpcs

.. code-block:: python

   {
     "data": {}
   }

Query actions are represented by dictionaries with a key ``query``. The simplest query payload ``{"model": "dataset"}`` asks for all entries of a single entity, in this case dataset. The valid entities are ``dataset``, ``file``, ``comment``, ``tag``, ``user``, and ``group``. Additionally, the API supports querying collections using ``collection:<name>``, where ``<name>`` denotes configured collection name. The complete HTTP request to get all datasets looks like:

.. code-block:: bash

   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"rpcs": [{"query": {"model": "dataset"}}]}' \
        $MARV_API/v1/rpcs

.. code-block:: python

   {
     "data": {
       "dataset": [
         {
           "id": 1,
           "collection": "bags",
           "discarded": 0,
           "name": "laser",
           "status": 0,
           "time_added": 1568903426121,
           "timestamp": 1521328251000,
           "setid": "dbgjsro7vfazyrj2pavoouk3vq"
         },
         // and many more ...
       }
     }
   }

Often not all attributes are required on the client side. To restrict the fields in the response the query payload can contain an ``attrs`` object. Its keys correspond to the database fields that should be returned, and its values are always set to ``true`` for real database columns.

.. code-block:: python

   {
     "model": "dataset",
     "attrs": {
       "name": true,
       "setid": true,
     },
   }

.. code-block:: python

   {
     "data": {
       "dataset": [
         {
           "name": "laser",
           "setid": "dbgjsro7vfazyrj2pavoouk3vq",
           "id": 1
         },
         {
           "name": "map",
           "setid": "ob56ua4ztunqeh7iw6ywg2ntum",
           "id": 2
         },
         {
           "name": "navsatfix",
           "setid": "g5nnjxaejquqrph6dnsencj2mi",
           "id": 3
         },
         {
           "name": "odom",
           "setid": "gl5zdundbwwsr2qhduous5324y",
           "id": 4
         },
         {
           "name": "test",
           "setid": "o6yufr25xqhx7nz7tljdr4ogaa",
           "id": 5
         }
       ]
     }
   }

The results can be filtered using the ``filters`` key. Its value is a list of filter objects to apply. Each filter object consists at least of an operator ``op``. Most operators are applied to a field ``name`` and work with a value ``value``. The following query payload gets the dataset where the field ``id`` equals 3:

.. code-block:: python

   {
     "model": "dataset",
     "filters": [
       {"op": "eq", "name": "id", "value": 3},
     ],
   }

.. code-block:: python

   {
     "data": {
       "dataset": [
         {
           "id": 3,
           "name": "navsatfix",
           // other attrs
         }
       ]
     }
   }

The filters list can contain multiple filter objects and by default the results have to match all. The following operators work on fields and values:

- ``between``: field is in the range of value ([low, high])
- ``endswith``: string field ends with value
- ``eq``: field equal to value, for comparison to ``null`` use ``is`` (see below)
- ``gt``: field greater than value
- ``gte``: field greater equal value
- ``in``: field is contained in list of values [val1, val2, ...]
- ``is``: field is value
- ``isnot``: field is not value
- ``lt``: field is lower than value
- ``lte``: field is lower equal value
- ``ne``: field is not equal value
- ``notbetween``: field is not in the range of value ([low, high])
- ``notin``: field is not one of the values in value [val1, val2, ...]
- ``startswith``: string field starts with value
- ``substring``: value is a substring of field

There are three additional operators that implement boolean logic to combine filters. Each of the operators works without a field name and operates on value only:

- ``not``: Negates val which is another filter object itself
- ``and``: "ANDs" all filter objects in a value list
- ``or``: "ORs" all filter objects in a value list

Filters can also operate on related tables by using a dotted path notation in field names. To search for datasets tagged ``important`` use:

.. code-block:: python

   {
     "model": "dataset",
     "filters": [
       {"op": "eq", "name": "tags.value", "value": "important"},
     ],
   }

.. code-block:: python

   {
     "data": {
       "dataset": [
         {
           "id": 1,
           "name": "laser",
           // other attrs
         }
       ]
     }
   }

A query can also embed related models into the response by setting its corresponding ``attrs`` key similarly to regular model fields. Set the value to ``true`` to embed complete objects or set the value to an object that shall be used as ``attrs`` for the related model:

.. code-block:: python

   {
     "model": "dataset",
     "attrs": {
       "name": true,
       "tags": {"value": true},  # populate tag objects only with value field
     },
     "filters": [
       {"op": "eq", "name": "tags.value", "value": "important"},
     ],
   }

.. code-block:: python

   {
     "data": {
       "dataset": [
         {
           "name": "laser",
           "id": 1,
           "tags": [
             1, 4
           ]
         }
       ],
       "tag": [
         {
           "value": "autonomous",
           "id": 1
         }
         {
           "value": "important",
           "id": 4
         }
       ]
     }
   }

The API supports sorting and paging. To sort the results use the option ``order`` with a value of ``["fieldname" "ORDER"]`` with ORDER being either ``ASC`` or ``DESC``. Paging is achieved with the ``limit`` and ``offset`` integer options. An example query payload would look like:

.. code-block:: python

   {
     "model": "dataset",
     "order": ["setid", "ASC"],  # sort ascending by setid
     "limit": 5,                 # limit number of results to 5
     "offset": 10,               # skip the first 10 results
   }


.. _httpapi_query_collection:

Collection
^^^^^^^^^^

The filter fields of each collection are available on virtual models on the Query endpoint. Querying the virtual model of a collection is achieved by setting the model parameter to ``collection:<name>``. The following rpc query payload gets the ``bags`` collection:

.. code-block:: python

   {
     "model": "collection:bags",
   }

Since each collection can have individually configured filters, the returned models will have different keys for different collections. All filter field names from the marv config are prefixed with ``f_`` in the query API. Depending on type of a filter its values are returned in one of two ways:

- column on the virtual model, if the value is a single scalar per dataset,
- relation to secondary model, if there can be multiple values per dataset (``string[]`` or ``subset`` filters).

All fields of scalar type are directly embedded on the collection models in the query response.

.. code-block:: python

   {
     "data": {
       "collection:bags": [
         {
           "id": 1
           "f_name": "laser",
           "f_setid": "dbgjsro7vfazyrj2pavoouk3vq",
           # other filter fields
         },
         # other items
       ],
     },
   }

Values of filter fields represented as a relation have to be requested specifically by name. If there is a field named ``topics``, it can be requested using the ``attrs`` key:

.. code-block:: python

   {
     "model": "collection:bags",
     "attrs": {"f_topics": true},
   }

The collection models in the response have a ``f_topics`` key, listing the related f_topic ids, and a top level ``f_topics`` list will contain the related values:

.. code-block:: python

   {
     "data": {
       "collection:bags": [
         {
           "id": 1
           "f_topics": [1, 2],
           # other filter fields
         },
         # other items
       ],
       "f_topics": [
         {
           "id": 1,
           "value": "/camA/jai/nir/camera_info",
         },
         {
           "id": 2,
           "value": "/camA/jai/nir/image_raw",
         },
         # other items
       ],
     },
   }

Filtering works as with any other model. For example, to find a collection entry by setid use:

.. code-block:: python

   {
     "model": "collection:bags",
     "filters": [{"op": "eq", "name": "f_setid", "value": "..."}]
   }

Multi-value fields can also be used in queries. For example, to find datasets including Image messages use:

.. code-block:: python

   {
     "model": "collection:bags",
     "filters": [{"op": "eq", "name": "f_msg_types.value", "value": "sensor_msgs/Image"}]
   }

Each collection entry corresponds to one dataset. For filtering by and embedding of relations belonging to the dataset itself -- namely ``file``, ``comment``, and ``tag`` -- the API supports the ``dataset.`` prefix.

.. code-block:: python

   {
     "model": "collection:bags",
     "filters": [
       {"op": "substring", "name": "dataset.comments.text", "value": "failure"},
       {"op": "eq", "name": "dataset.tags.value", "value": "autonomous"},
     ]
     "attrs": {"dataset.files"},
   }



Listing (deprecated, will be removed in 21.04)
----------------------------------------------

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


.. _httpapi_trigger:

Trigger Actions (EE)
--------------------

The trigger API allows to schedule actions. In case no action is running a triggered action will start immediately, otherwise right after the running action has finished. In both cases the HTTP request will remain open until the action has finished. There are two actions ``scan`` and ``run``, which wrap the corresponding CLI commands and return a mapping with ``returncode``, ``stdout``, and ``stderr``; ``returncode == 0`` means success. In case of server-side errors only an ``error`` field is returned.


Scan
^^^^

The scan action schedules a scan of all configured scanroots.

.. code-block:: bash

   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
	-d '{"action": "scan"}' \
	$MARV_API/v1/trigger

Example output:

.. code-block:: python

   {"returncode": 0, "stdout": "...", "stderr": ""}

The ``stdout`` field will contain the same MARV log messages a scan on the CLI would produce.


Run
^^^

The run action schedules a run of all configured nodes on a specific dataset.

.. code-block:: bash

   curl -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
	-d '{"action": "run", "dataset": "xy5ba2hy2hr5453m6ftokk6kdq"}' \
	$MARV_API/v1/trigger

Example output:

.. code-block:: python

   {"returncode": 0, "stdout": "...", "stderr": ""}

If all nodes have already been run on this dataset the action does nothing and returns immediately indicating successful completion.
