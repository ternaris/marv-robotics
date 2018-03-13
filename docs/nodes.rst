.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _nodes:

Nodes
=====

Bag metadata
------------

.. autofunction:: marv_robotics.bag.bagmeta()


ROS bag messages
----------------

.. autofunction:: marv_robotics.bag.raw_messages()
.. autofunction:: marv_robotics.bag.get_message_type


Images
------

.. autofunction:: marv_robotics.cam.images()


Video
-----

.. autofunction:: marv_robotics.cam.ffmpeg()


Fulltext
--------

.. autofunction:: marv_robotics.fulltext.fulltext()


GNSS
----
.. autofunction:: marv_robotics.gnss.positions()
.. autofunction:: marv_robotics.gnss.imus()
.. autofunction:: marv_robotics.gnss.navsatorients()
.. autofunction:: marv_robotics.gnss.orientations()
.. autofunction:: marv_robotics.gnss.gnss_plots()


Trajectory
----------

.. autofunction:: marv_robotics.trajectory.navsatfix()

.. autofunction:: marv_robotics.trajectory.trajectory()


.. _widget_nodes:

Widget nodes
------------

Widgets are used by sections or are rendered in the special summary sections when configured in the :ref:`cfg_c_detail_summary_widgets` config key.

.. autofunction:: marv_robotics.detail.bagmeta_table()
.. autofunction:: marv_robotics.detail.summary_keyval()
.. autofunction:: marv_robotics.detail.galleries()


.. _section_nodes:

Section nodes
-------------

.. autofunction:: marv_robotics.detail.images_section()
.. autofunction:: marv_robotics.detail.connections_section()
.. autofunction:: marv_robotics.detail.trajectory_section()
.. autofunction:: marv_robotics.detail.video_section()
.. autofunction:: marv_robotics.detail.gnss_section()
