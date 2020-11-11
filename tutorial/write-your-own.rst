.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _write-your-own:

Tutorial: Write your own nodes
==============================

Within MARV, nodes are responsible to extract and process data from your log files as base for filtering and visualization. MARV Robotics already ships with a set of nodes (:mod:`marv_robotics`). Here, you find a quick tutorial on writing your own.

All code and configuration of this tutorial is included with your release of MARV Robotics EE in the top-level ``tutorial`` folder.


Prerequisites
-------------

- :ref:`install`
- :ref:`setup-basic-site`


Create python package
---------------------

First, you need a python package to hold the code of your nodes. A good name for that package might be your company's name suffixed with ``_marv``:

.. code-block:: console

  $ mkdir code/company_marv  # directory holding python distribution
  $ cp tutorial/code/setup.py code/company_marv/

  $ mkdir code/company_marv/company_marv  # directory holding python package
  $ touch code/company_marv/company_marv/__init__.py

It might make sense that the distribution directory name matches the name provided in ``setup.py`` (see below). There, also the python package directory is listed as ``packages`` -- it must not contain dashes but may contain underscores. One python distribution can contain many packages. At some point you might want to dive into `Python Packaging <https://python-packaging.readthedocs.io/en/latest/>`_

We placed the Python code of this tutorial into the public domain, so you can freely pick from it.  Beware, not to copy the license file and headers and adjust ``setup.py`` accordingly, except if you intend to release your code into the public domain as well:

**setup.py**

.. literalinclude:: code/setup.py
..    :caption: setup.py
..    :emphasize-lines: 1-11, 17,19,21-24

Next, it's a good idea to place this code under version control:

.. code-block:: console

  $ cp tutorial/code/.gitignore code/company_marv/
  $ git checkout -b custom
  $ git add code/company_marv
  $ git commit -m 'Add empty company_marv package'

Finally, for marv to make use of your nodes, you need to install the package into the virtual python enviroment. Install it in development mode (``-e``) for changes to be picked up without the need to reinstall. Activate the virtualenv first, if it is not already activated. Most of the time we use just ``$`` as prompt you can run the commands also with an activated virtualenv, creating a virtualenv being a notable exception. In case we use ``(venv) $`` as prompt, it has to be activated:

.. code-block:: console

  $ source venv/bin/activate
  (venv) $ pip install -e code/company_marv

**docker**:

Tell container to run ``marv init`` and install all code in development mode.

.. code-block:: console

   $ MARV_INIT=1 DEVELOP=1 ./scripts/run-container site site/scanroot


First node: Extract an image
----------------------------

For sake of simplicity, we are placing all code directly into the package's ``__init__.py``. Later you might want to split this up into individual modules or `packages <https://docs.python.org/2/tutorial/modules.html#packages>`_. Following is the full code of the image extraction node. We'll be dissecting it shortly.

**marv_tutorial/__init__.py**

.. literalinclude:: code/marv_tutorial/__init__.py
    :lines: 4-16
.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: image

At first glance, there are three blocks of imports: python standard library, external libraries, and own project. Further, there we define a topic used during the tutorial and a node seems to be based on a Python generator function that uses :any:`yieldexpr`.

Let's look at this, piece-by-piece.


.. _tutorial_declare_image_node:

Declare image node
^^^^^^^^^^^^^^^^^^

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: image
    :lines: -12

We are declaring a ``marv.node`` using `decorator syntax <https://www.python.org/dev/peps/pep-0318/#motivation>`_ based on a function named ``image``, which becomes also the name of the node. The node will output ``File`` messages and consume a selected topic of raw messages as input stream ``cam``. According to the docstring it will return the first image of this stream. The docstring is following the `Google Python Style Guide <http://google.github.io/styleguide/pyguide.html>`_ which is understood by `Sphinx <http://www.sphinx-doc.org/en/stable/>`_ using `Napoleon <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/>`_ to generate documentation.


Yield to interact with marv
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: image
    :lines: 13-17

The input stream's topic is set as title for the image node's output stream and we are pulling the first message from the input stream. In case there is none, we simply return without publishing anything.

:any:`yieldexpr` turn Python functions into generator functions. In short: ``yield`` works like ``return``, but preserves the function state to enable the calling context -- the marv framework -- to reactivate the generator function and resume operation where it left as if it were a function call with optional return value. In case of the second line marv sends the first message of the ``cam`` input stream as response to the ``marv.pull``, which will be assigned to the ``msg`` variable and operation continues within the image node until the next ``yield`` statement or the end of the function.


Deserialize raw message
^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: image
    :lines: 19-22

The ``raw_messages`` node pushes raw ROS messages, which have to be deserialized using the correct message type returned by :any:`get_message_type`.


Write image to file
^^^^^^^^^^^^^^^^^^^

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: image
    :lines: 24-

Define name for the image file and instruct marv to create a file in its store. Then transform the ros image message into an opencv image and save it to the file. Finally, push the file to the output stream for consumers of our image node to pull it.

Next, we'll create a detail section that pulls and displays this image.


Show image in detail section
----------------------------

In order to show an image in a detail section, the section needs to be coded and added to the configuration along with the image node created in the previous section.

Code
^^^^

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: image_section

The ``image_section`` node's output stream contains messages of type ``Section``. It consumes one input parameter ``title`` with a default value of ``Image`` as well as the output stream of the ``image`` node declared previously. In case the ``image`` node did not push any message to its output stream, we simply return, without creating a section.

Otherwise, a widget of type ``image`` is created and finally a section containing this image is pushed to the output stream.

Next, we are adding our nodes to the configuration.

Config
^^^^^^

**marv.conf**

.. literalinclude:: write-your-own0/marv.conf
    :emphasize-lines: 14-15,22

.. note::

   Remember to stop ``marv serve``, run ``marv init``, and start ``marv serve`` again.


Run nodes
^^^^^^^^^

.. code-block:: console

  (venv:~/site) $ marv run --collection=bags
  INFO marv.run qmflhjcp6j.image_section.io4thnkdxx.default (image_section) started
  INFO marv.run qmflhjcp6j.image.og54how3rb.default (image) started
  INFO marv.run qmflhjcp6j.image.og54how3rb.default finished
  INFO marv.run qmflhjcp6j.image_section.io4thnkdxx.default finished
  INFO marv.run vmgpndaq6f.image_section.io4thnkdxx.default (image_section) started
  INFO marv.run vmgpndaq6f.image.og54how3rb.default (image) started
  INFO marv.run vmgpndaq6f.image.og54how3rb.default finished
  INFO marv.run vmgpndaq6f.image_section.io4thnkdxx.default finished

Et voilà. Reload your browser (http://localhost:8000) and you should see the detail section with an image. Let's extract multiple images!

**docker**: Run commands inside container, after entering it with ``./scripts/enter-container``.


Display gallery of images
-------------------------

To display a gallery of images, we'll be using another two nodes, again one for extraction and one for the section and add them to the configuration.

Code
^^^^

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: images
    :emphasize-lines: 16-22,31

Instead of only the first image, we now want to extract the first 20 images. We are using a ``while`` loop and are breaking if either the input stream is exhausted or 20 images are extracted -- :paramref:`marv.pull.enumerate` saves us from counting manually. A ``name_template`` together with the index produces unique and meaningful filenames to store the images. All other elements you know already from the ``images`` node above. Let's create a section to display the images.

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: gallery_section
    :emphasize-lines: 3,20-22,25

The ``gallery_section`` depends on the just created ``images`` node. To pull all images, it also uses a while loop and while in the ``image_section`` we returned an ``image`` widget, this time we use a ``gallery`` widget with a list of ``images``. Let's add the new nodes to the config file and run them. Marv determines which nodes' output is missing from the store and runs only these. By default it checks all nodes being listed in ``detail_summary_widgets`` and ``detail_sections``. Actually, there are two more config keys, but they will be part of a future tutorial. Dependencies will be automatically added as needed.

Config
^^^^^^

.. literalinclude:: write-your-own1/marv.conf
    :emphasize-lines: 16-17,25

.. note::

   Remember to stop ``marv serve``, run ``marv init``, and start ``marv serve`` again.

.. code-block:: console

  (venv:~/site) $ marv run --collection=bags
  INFO marv.run qmflhjcp6j.gallery_section.oamfub7jpa.default (gallery_section) started
  INFO marv.run qmflhjcp6j.images.og54how3rb.default (images) started
  INFO marv.run qmflhjcp6j.images.og54how3rb.default finished
  INFO marv.run qmflhjcp6j.gallery_section.oamfub7jpa.default finished
  INFO marv.run vmgpndaq6f.gallery_section.oamfub7jpa.default (gallery_section) started
  INFO marv.run vmgpndaq6f.images.og54how3rb.default (images) started
  INFO marv.run vmgpndaq6f.images.og54how3rb.default finished
  INFO marv.run vmgpndaq6f.gallery_section.oamfub7jpa.default finished

Et voilà. Reload your browser (http://localhost:8000) and you should see the gallery section.

Let's move to the final piece of this tutorial: a section combining multiple widgets and introducing two more widget types: tables and plots.


.. _tutorial_combined:

Combined: table, plot and gallery
---------------------------------

In the final section we want to display a table that lists name and size of the image files, a plot of the filesizes, and again the gallery. To this end we create a stream of filesizes, the plot and the combined section:

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: filesizes
    :emphasize-lines: 1

"Computing" the filesizes is so cheap, that we do not want to store the node's output and therefore don't need to specify a schema and are able to return arbitrary python objects (more on this later).

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: filesize_plot
    :emphasize-lines: 12-23, 25-28, 30-38, 40-48

There are different approaches to show plotted data in the frontend and here we will showcase three, namely ``plotly``, ``mpld3`` and ``image``.

`Plotly <https://plotly.com/python/>`_ is a graphing library for browser-based interactive graphs. Here we use Plotly's Python interface to create a figure object from the filesize data. After serializing the figure into a JSON file, we create a Plotly widget referencing said file.

`Matplotlib <https://matplotlib.org/>`_ is a widely adopted graphing library in the Python ecosystem. Similar to the Plotly approach we first create a matplotlib figure from the data. Since matplotlib has no builtin support for browser-based plots, we use the `mpld3 <http://mpld3.github.io/>`_ serialization library to export the plot to a JSON file. Mirroring the plotly approach again, we create a mpld3 widget referencing the exported data. Matplotlib has builtin support to export a figure object as an image. Here we choose to export the figure into a ``jpg`` file and display using an image widget, like we have seen before.

Finally, the different plotting outputs are nested into a ``dropdown`` widget, allowing the user to switch between different visualizations.

.. literalinclude:: code/marv_tutorial/__init__.py
    :pyobject: combined_section
    :emphasize-lines: 12-15,23-27,33

New is the ``table`` widget here, defined by ``rows`` and ``columns``. The columns have title to be displayed for the column as well as a formatter that is responsible to display the content of each cell of a column. A row has ``cells``, which is a list of values being formatted by the formatters.

.. literalinclude:: write-your-own2/marv.conf
    :emphasize-lines: 18,27

.. note::

   Remember to stop ``marv serve``, run ``marv init``, and start ``marv serve`` again.

.. code-block:: console

  $ marv run --collection=bags
  INFO marv.run qmflhjcp6j.combined_section.ft6zlxpbvn.default (combined_section) started
  ERRO marv.cli Exception occured for SetID('qmflhjcp6j3hsq7e56xzktf3yq'):
  Traceback (most recent call last):
  ...
  marv_node.driver.MakeFileNotSupported: <VolatileStream qmflhjcp6j.filesize_plot.cpenbxihfq.default>

There was an error: The ``filesize_plot`` requested to make a file, but marv failed to follow through. Nodes can be persistent or volatile. Persistent nodes are stored in marv's store, need to declare a schema (i.e. ``Section`` or ``Widget``) and be listed in ``marv.conf``. Volatile nodes need none of that and are run every time somebody needs them. The ``filesize`` node for example is cheap to run, even pointless beyond the scope of a tutorial, and therefore volatile: not listed in ``marv.conf`` and declaring no schema, just ``@marv.node()``.

For nodes to be able to make files, they need to be persistent. We forgot to add ``filesize_plot`` to ``marv.conf``:

.. literalinclude:: write-your-own3/marv.conf
    :emphasize-lines: 18

.. note::

   Remember to stop ``marv serve``, run ``marv init``, and start ``marv serve`` again.

.. code-block:: console

  $ marv run --collection=bags
  INFO marv.run qmflhjcp6j.combined_section.ft6zlxpbvn.default (combined_section) started
  INFO marv.run qmflhjcp6j.filesize_plot.cpenbxihfq.default (filesize_plot) started
  INFO marv.run qmflhjcp6j.filesize_plot.cpenbxihfq.default finished
  INFO marv.run qmflhjcp6j.combined_section.ft6zlxpbvn.default finished
  INFO marv.run vmgpndaq6f.bagmeta_table.gahvdc4vpg.default (bagmeta_table) started
  INFO marv.run vmgpndaq6f.combined_section.ft6zlxpbvn.default (combined_section) started
  INFO marv.run vmgpndaq6f.gallery_section.oamfub7jpa.default (gallery_section) started
  INFO marv.run vmgpndaq6f.image_section.io4thnkdxx.default (image_section) started
  INFO marv.run vmgpndaq6f.connections_section.yjrewalqzc.default (connections_section) started
  INFO marv.run vmgpndaq6f.bagmeta.dwz4xbykdt.default (bagmeta) started
  INFO marv.run vmgpndaq6f.filesize_plot.cpenbxihfq.default (filesize_plot) started
  INFO marv.run vmgpndaq6f.images.og54how3rb.default (images) started
  INFO marv.run vmgpndaq6f.image.og54how3rb.default (image) started
  INFO marv.run vmgpndaq6f.bagmeta.dwz4xbykdt.default finished
  INFO marv.run vmgpndaq6f.connections_section.yjrewalqzc.default finished
  INFO marv.run vmgpndaq6f.bagmeta_table.gahvdc4vpg.default finished
  INFO marv.run vmgpndaq6f.image.og54how3rb.default finished
  INFO marv.run vmgpndaq6f.image_section.io4thnkdxx.default finished
  INFO marv.run vmgpndaq6f.images.og54how3rb.default finished
  INFO marv.run vmgpndaq6f.gallery_section.oamfub7jpa.default finished
  INFO marv.run vmgpndaq6f.filesize_plot.cpenbxihfq.default finished
  INFO marv.run vmgpndaq6f.combined_section.ft6zlxpbvn.default finished

**docker**: Run commands inside container, after entering it with ``./scripts/enter-container``.


Persistent nodes and custom output types
----------------------------------------

If nodes do not declare an output message type ``@marv.node()`` they are volatile, will run each time somebody needs them, and they can output arbitrary python objects. In order to use node output in :ref:`cfg_c_listing_columns` or :ref:`cfg_c_filters`, the node needs to be persistent. In order to persist a node in the store it needs to declare an output type ``@marv.node(TYPE)`` and be listed in :ref:`cfg_c_nodes`. MARV uses `capnp <https://capnproto.org/>`_ to serialize and persist messages and ships with a couple of pre-defined types, which are available via ``marv.types``. Please take a look at that module and the capnp files it is importing from.

In order to create your own capnp message types, place a ``module.capnp`` next to your ``module.py`` and take a look at the capnp files shipping with marv as well as the capnp `schema language <https://capnproto.org/language.html>`_.


Summary
-------

You learned to create a python package and wrote your first nodes to extract images, create a plot and table, and display these in detail sections.

Happy coding!
