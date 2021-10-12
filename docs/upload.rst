.. Copyright 2020-2021  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _upload:

Upload (EE)
===========

MARV processes and manages continuous recordings performed by large fleets of robots. To ease the handling of a large influx of data MARV implements an upload functionality. It takes care that new data is quickly and securely handed into MARV management. Transmissions are automatically authenticated and encrypted.

In the MARV ecosystem data providers that connect to the MARV server are called *leaves*. A leaf can be any potential source of data, e.g. a robot, vehicle, CI server, local simulator, or any other technical system.

Preparations
------------

For secure operation some preparatory steps are necessary.

- Create leaf in MARV via web leaf admin panel or CLI
- Generate authentication token for leaf via web leaf admin panel or CLI
- Download ``marv-leaf`` binary from web leaf admin panel, copy to robot, and rename
- Register robot as MARV leaf using the authentication token

Example to add a leaf and generate its token via CLI::

  (server)$ marv leaf add C3P0
  (server)$ marv leaf regen-token C3P0
  New token for C3P0: <secret_token>

And use the token to register the leaf::

  (leaf)$ marv-leaf register https://example.com
  Token: <secret_token>
  Registered successfully as leaf 'C3P0'.

The leaf binaries are statically linked and have no other dependencies. They contain system and architecture in their names, please feel free to rename them to just ``marv-leaf`` when copying them to the leaf system.

Once installed the leaf binary is able to update itself from a running MARV server. This is not necessary with every MARV release, instead ``marv-leaf`` will inform you if an update is necessary.


Upload datasets
---------------

Once server and leaf have been prepared uploading datasets to MARV is straightforward.

::

   (leaf)$ marv-leaf upload --collection bags recording.bag

This command will upload the file ``recording.bag`` to the MARV instance ``example.com`` and add the dataset to the ``bags`` collection.

Upload multiple files as one dataset by placing them into one directory and pass this to ``marv-leaf upload``. For rosbag2 place additional files into the directory first.

To upload multiple datasets call the command multiple times. See ``marv-leaf upload --help`` for more information.


Metadata / userdata
^^^^^^^^^^^^^^^^^^^

Optionally, pass a json file ``marv-leaf upload --meta meta.json ...`` containing one top-level ``userdata`` key with dictionary value. This *userdata* is available as ``dataset.userdata`` in nodes and config functions.

Multiple uploads may use the same metadata file, the file name is not important, but the file must not reside in the directory to be uploaded.


Return code
^^^^^^^^^^^

On success the return value will be zero and the upload process will have made sure that the checksums of all uploaded files are correct.

Rerunning ``marv-leaf upload`` on the same set of files will not create another dataset. Instead the MARV will recognize that the data already exists on the server and will indicate success by returning zero.

If an upload is interrupted manually e.g. by loss of network connectivity, the return value will be non-zero to indicate failure. Rerunning ``marv-leaf upload`` with the same parameters will resume the upload from where it was interrupted.


Data safety
-----------

Leaves upload datasets to :ref:`cfg_marv_leavesdir`. Make sure to include this directory in backups and consider to delete datasets on leaves only after sufficient time has passed for them to be in backup as well.


Access control
--------------

Uploaded datasets are only visible to admins by default. For a normal user to see a dataset, she needs to receive permissions first through group membership. See :ref:`eeacl` for more information.
