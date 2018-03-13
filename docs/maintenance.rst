.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _maintenance:

Maintenance
===========

Cleanup
-------

When searching for tags and other ``subset`` :ref:`cfg_c_filters`, marv presents lists of existing tags. To present only used items, these lists need to be regularly cleaned-up.

.. code-block:: bash

   marv cleanup --unused-tags


When datasets are deleted (via frontend, API, cli) they are only marked as discarded and can be "undiscarded".

.. code-block:: bash

   marv undiscard --help

To actually delete these

.. code-block:: bash

   marv cleanup --discarded

Additional cleanup operations will be added in one of the next releases.
