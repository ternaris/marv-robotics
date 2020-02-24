.. Copyright 2020  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _upload:

Upload (EE)
===========

MARV is designed to process and manage continuous recordings performed by large fleets of robots. To ease the handling of a large influx of data MARV implements an upload functionality. It takes care that new data is quickly and securely handed into MARV management. Transmissions are automatically authenticated and encrypted.

In the MARV ecosystem data providers that connect to the MARV server are called ``leafs``. A leaf can be any potential source of data, e.g. a robot, a vehicle, a CI server, or any other technical system.

Preparations
------------

For secure operation some preparational steps are necessary.

Create a leaf
^^^^^^^^^^^^^

To upload data to MARV the data providing robot has to be registered as a leaf.

::

   (server)$ marv leaf add C3P0

Generate an authentication token
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

MARV does not allow anonymous uploads and all connections have to be authenticated. This is achieved by generating tokens on the server and storing those on the leafs.

::

   (server)$ marv leaf regen-token C3P0
   New token for C3P0: <secret_token>

Store token on leaf
^^^^^^^^^^^^^^^^^^^

The freshly created token has to be stored on the leaf. The command will prompt twice to paste the string from the server.

::

   (leaf)$ marv set-leaf-token
   Token: <secret_token>
   Repeat for confirmation: <secret_token>

Upload datasets
---------------

Once server and leaf have been prepared uploading datasets to MARV is straightforward.

::

   (leaf)$ marv upload --url https://example.com --collection bags recording.bag

This command will upload the file ``recording.bag`` to the MARV instance ``example.com`` and add the dataset to the ``bags`` collection. It is possible to specify any number of files to upload as a singular dataset. To upload multiple datasets call the command multiple times.

Return code
^^^^^^^^^^^

On success the return value will be zero and the upload process will have made sure that the checksums of all uploaded files are correct.

Rerunning ``marv upload`` on the same set of files will not create another dataset. Instead the MARV will recognize that the data already exists on the server and will indicate success by returning zero.

If an upload is interrupted manually of by e.g. loss of network connectivity the return value will be non zero to indicate failure. Rerunning ``marv upload`` with the same parameters will resume the upload from where it was interrupted.

Data safety
-----------

The uploaded datasets are stored in a subdirectory ``leaf`` in the collection's scanroot. Independent of the upload feature all scanroots need to be backed up regularly, e.g. via cronjob. In addition to that a list of checkpoint commands can be run before MARV touches the scanroot as part of an upload. Please see :ref:`cfg_upload_checkpoint_commands` for more information.
