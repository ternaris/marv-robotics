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

   (leaf)$ marv-leaf upload --collection bags --name recording recording.bag

This command will upload the file ``recording.bag`` to the MARV instance ``example.com`` and add the dataset to the ``bags`` collection. It is possible to specify any number of files to upload as a singular dataset. To upload multiple datasets call the command multiple times. For rosbag2 directories pass the path to the directory and place additional files into the directory first.

Return code
^^^^^^^^^^^

On success the return value will be zero and the upload process will have made sure that the checksums of all uploaded files are correct.

Rerunning ``marv-leaf upload`` on the same set of files will not create another dataset. Instead the MARV will recognize that the data already exists on the server and will indicate success by returning zero.

If an upload is interrupted manually e.g. by loss of network connectivity, the return value will be non-zero to indicate failure. Rerunning ``marv-leaf upload`` with the same parameters will resume the upload from where it was interrupted.


Data safety
-----------

The uploaded datasets are stored in a site's :ref:`cfg_marv_leavesdir`, by default ``leaves``. Independent of the upload feature all scanroots and the leaves directory need to be backed up regularly, e.g. via cronjob. In addition to that a list of checkpoint commands can be run before MARV touches the leaves directory as part of an upload. Please see :ref:`cfg_upload_checkpoint_commands` for more information.


Access control
--------------

Uploaded datasets are only visible to admins by default. For a normal user to see a dataset, she needs to receive permissions first through group membership. See :ref:`eeacl` for more information.
