.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _widgets:

Widgets
=======

The frontend detail view consists of sections displayed as tabs containing widgets. Specific nodes produce the output rendered by the frontend into sections and widgets. See :ref:`write-your-own` for an introduction to this.

:ref:`section_nodes` are decorated with ``@marv.node(Section)`` and push a dictionary with title and a list of widgets:

.. code-block:: python

   section = {'title': 'Section title', 'widgets': [widget, ...]}

:ref:`widget_nodes` are decorated with ``@marv.node(Widget)`` and push a dictionary with an optional title and one key corresponding to a ``widget_type`` (e.g. ``image``) and ``value`` with data extracted from a dataset to be rendered by the widget (e.g. ``{'src': 'img/path'}``.

.. code-block:: python

   widget = {'title': 'Widget title', widget_type: data}

Widgets are either rendered directly into a section or are used as part of another composite widget, e.g. an ``image`` in a ``gallery`` (see below).

Valid values for ``widget_type`` are given in the following sections. The ``title`` key is optional and omitted for brevity.


.. _widget_image:

Image
^^^^^
.. code-block:: python

   image = {'image': {'src': img.relpath}}

Example: Image used inside gallery :func:`marv_robotics.detail.galleries`


.. _widget_gallery:

Gallery
^^^^^^^
.. code-block:: python

   gallery = {'gallery': {'images': [image, ...]}}

Example: :func:`marv_robotics.detail.galleries`


.. _widget_video:

Video
^^^^^
.. code-block:: python

   video = {'video': {'src': videofile.relpath}}

Example: :func:`marv_robotics.detail.video_section`


.. _widget_pdf:

PDF (EE)
^^^^^^^^
.. code-block:: python

   pdf = {'pdf': {'src': pdffile.relpath}}


.. _widget_dropdown:

Dropdown
^^^^^^^^
.. code-block:: python

   dropdown = {'dropdown': {'widgets': [
       {'title': '/cam1', 'video': {'src': videofile.relpath}},
       {'title': '/cam2', 'video': {'src': videofile.relpath}},
   ]}}

A dropdown menu selects one of a list of widgets to be displayed below; their titles are displayed in the dropdown.


.. _widget_plotly:

Interactive Plots
^^^^^^^^^^^^^^^^^

There are two options for plotting:
  - `matplotlib <https://matplotlib.org/>`_ with `mpld3 <https://mpld3.github.io/>`_; see :ref:`tutorial_combined`
  - `plotly <https://plotly.com/python/>`_ see below

.. code-block:: python

    import plotly.graph_objects as go

    # plot into figure with plotly
    fig = go.Figure(data=go.Scatter(y=distances))

    # save plotly figure to file
    plotfile = yield marv.make_file('distances.json')
    Path(plotfile.path).write_text(fig.to_json())

    # create plotly widget referencing file
    yield marv.push({
        'title': 'Distance driven',
        'plotly': f'marv-partial:{plotfile.relpath}',
    })


.. _widget_trajectory:

Trajectory
^^^^^^^^^^
The trajectory widget renders a list of layers on top of each other.

.. code-block:: python

   {'zoom': {'min': -10, 'max': 30},
    'layers': [
        {'title': 'Vector floor map',
         'geojson': geojson_object1},
        {'title': 'Trajectory',
         'color': (0., 1., 0., 1.),
         'geojson': geojson_object2},
    ]
   }

The zoom value defines the valid zoom range that will be enforced in the frontend. Each layer in the list is defined by its name that is displayed in the legend, an optional legend color, and its GeoJSON definition.

The geojson value conforms the official `GeoJSON format specification <https://tools.ietf.org/html/rfc7946>`_, and adds a few styling extensions. For now the widget supports a subset of the GeoJSON standard. The widget expects a feature collection as the toplevel GeoJSON object and the supported geometries are `LineString` and `Polygon`.

.. code-block:: python

   {'feature_collection': {'features': [
    {'geometry': {'line_string': {'coordinates': coord_list}},
     'properties': {'coordinatesystem': 'WGS84',      # or `cartesian`
                    'color': (0., 1., 0., 1.),        # per geometry color
                    'colors': color_list,             # or per vertex color list
                    'fillcolor': (0., 1., 0., 1.),    # per geometry fillcolor
                    'fillcolors': fillcolor_list,     # or per vertex fillcolor list
                    'width': 4.,                      # line or polygon stroke width
                    'timestamps': timestamp_list,     # per vertex timestamp used for playback
                    'rotations': rotations_list,      # per vertex rotations if markers are used
                    'markervertices' marker_geometry, # rotation marker polygon (e.g. `[0, 0, -1, .3, -1, -.3]`)
                    }},
   ]}}

The properties object holds styling and animation information for the trajectory player widget. Properties should at least define one of the color values, apart from that all entries are optional. The default coordinatesystem is `WGS84` which is used per default in the GeoJSON standard and in `sensor_msgs/NavSatFix Message`. The value `cartesian` allows the use of any Cartesian coordinate system.

`Colors` can be given either as a per geometry value or as a list of values for each vertex in the geometry.

The `width` value corresponds to the rendered line width in pixels. When the geometry is of type `polygon` and either of `color` or `colors` is set, then a stroke of width pixels is rendered.

*EE only:* The presence of a `timestamps` list enables the player functionality. This option works only with geometries of type `LineString` and should hold one value per geometry vertex. The widget assumes that the timestamps are in ascending order, as usually delivered by a GPS sensor.

*EE only:* The presence of a `markervertices` enables rendering of a marker at the current trajectory location during playback. The triangle size is not affected by zoom. If not set explicitly its rotation is calculated by the last significant heading from the coordinates.

*EE only:* The `rotations` list can be used to set the rotation of the marker at each coordinate. Each value is a scalar indicating the rotation around the z axis, e.g. obtained from an IMU. The rotation angles have to be given counter clock wise in radians, with zero pointing in the direction of the x axis.

Example: :func:`marv_robotics.detail.trajectory_section`


.. _widget_table:

Table
^^^^^
Example: :func:`marv_robotics.detail.bagmeta_table`


.. _widget_keyval:

Key/value
^^^^^^^^^
Example: :func:`marv_robotics.detail.summary_keyval`


.. _widget_pre:

Preformatted
^^^^^^^^^^^^
Wraps data into an html ``<pre></pre>`` tag.

.. code-block:: python

   pre = {'pre': {'text': 'foo\nbar'}}


.. _widget_custom:

Custom
^^^^^^
Renders custom widgets.

.. code-block:: python

   custom = {'custom': {'type': 'foo', 'data': json.dumps(data)}}

Create ``site/frontend/custom.js`` and restart your instance to customize widgets and formatters.

.. literalinclude:: config/custom.js
   :language: javascript

Beginning with MARV :ref:`v18.04` frontend styling is not based on Bootstrap v3 anymore. MARV now uses a custom style sheet with markup that is heavily inspired by Bootstrap v4 and is still undergoing improvements. Custom widgets can make use of existing CSS classes to achieve an identical look and feel to the native widgets. If stability is key, it is advisable to style custom widgets independently of MARV with their own style sheets to avoid migration pains during future MARV updates. Each widget is rendered in a container with the CSS class ``.widget-${name}``, and any custom CSS should be scoped to children of these containers.

Custom CSS is loaded from ``site/frontend/custom.css`` and ``site/frontend/custom/`` is mapped to the ``/custom/`` backend route to serve additional files.
