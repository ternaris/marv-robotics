.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _views:

Views
=====

The frontend shipping with marv features:

- a listing view served at the root of the application,
- a detail view to introspect individual data sets

Listing and detail view are specific to the selected collection. The displayed collection is selected via a drop-down in the header.


Listing
-------

The listing view consists of the following sections:

- A filter section that determines the data sets loaded from the server into the listing view (see :ref:`cfg_c_filters`).
- A summary on the loaded data sets (see :ref:`cfg_c_listing_summary`).
- A set of fancy filter widgets to refine the search on loaded data sets (EE only). For the default set of filter widgets to appear all of the following :ref:`cfg_c_listing_columns` need to be available: ``size``, ``added``, ``start_time``, ``end_time``, and ``duration``.
- A table listing the matching data sets (see :ref:`cfg_c_listing_columns`)


Detail
------

In order to introspect individual data sets, the first listing column is usually configured to route to the detail view.

The detail view consists of :ref:`cfg_c_detail_sections` organized as tabs. The first section is special in that it always exists. It displays a list of :ref:`cfg_c_detail_summary_widgets` and widgets for tagging and commenting.
