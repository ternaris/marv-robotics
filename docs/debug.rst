.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _debug:

Debugging
=========

Given an exception during a node run:

.. code-block:: console

   $ marv run --node bagmeta b563ng6y6d3 --force
   2018-02-01 09:58:10,552 INFO rospy.topics topicmanager initialized
   2018-02-01 09:58:10,984 INFO marv.run b563ng6y6d.bagmeta.dwz4xbykdt.default (bagmeta) started with force
   2018-02-01 09:58:10,987 ERRO marv.cli Exception occured for dataset b563ng6y6d3pjf6ycx7t52pqae:
   Traceback (most recent call last):
     File "/webapp/marv/suite/marv/marv/cli.py", line 405, in marvcli_run
       excluded_nodes, cachesize=cachesize)
     File "/webapp/marv/suite/marv/marv/site.py", line 351, in run
       deps=deps, cachesize=cachesize)
     File "/webapp/marv/suite/marv/marv_node/run.py", line 63, in run_nodes
       done, send_queue_empty = process_task(current, task)
     File "/webapp/marv/suite/marv/marv_node/run.py", line 352, in process_task
       return loop()
     File "/webapp/marv/suite/marv/marv_node/run.py", line 242, in loop
       promise = current.send(send)
     File "/webapp/marv/suite/marv/marv_node/driver.py", line 89, in _run
       request = gen.send(send)
     File "/webapp/marv/suite/marv/marv_node/node.py", line 243, in invoke
       send = yield gen.send(send)
     File "/webapp/marv/suite/robotics/marv_robotics/bag.py", line 171, in bagmeta
       xx
   NameError: global name 'xx' is not defined
   2018-02-01 09:58:10,992 ERRO marv.cli Error occured for dataset b563ng6y6d3pjf6ycx7t52pqae: global name 'xx' is not defined

one can enter pdbpp by running ``PDB=1 marv`` instead of ``marv``:

.. code-block:: console

   $ PDB=1 marv run --node bagmeta b563ng6y6d3 --force
   2018-02-01 13:04:41,524 INFO rospy.topics topicmanager initialized
   2018-02-01 13:04:41,979 INFO marv.run b563ng6y6d.bagmeta.dwz4xbykdt.default (bagmeta) started with force
   NameError("global name 'xx' is not defined",)
   /webapp/venv/lib/python2.7/site-packages/IPython/core/debugger.py:243: DeprecationWarning: The `color_scheme` argument is deprecated since version 5.1
     DeprecationWarning)
   > /webapp/marv/suite/robotics/marv_robotics/bag.py(171)bagmeta()
       170     end_time = 0
   --> 171     xx
       172     connections = {}

   (Pdb++)

Likewise pdb can be used by placing ``import pdb; pdb.set_trace()`` anywhere in the code.

.. code-block:: console

   $ marv run --node bagmeta b563ng6y6d3 --force
   2018-02-01 13:08:14,235 INFO rospy.topics topicmanager initialized
   2018-02-01 13:08:14,633 INFO marv.run b563ng6y6d.bagmeta.dwz4xbykdt.default (bagmeta) started with force
   /webapp/venv/lib/python2.7/site-packages/IPython/core/debugger.py:243: DeprecationWarning: The `color_scheme` argument is deprecated since version 5.1
     DeprecationWarning)
   > /webapp/marv/suite/robotics/marv_robotics/bag.py(172)bagmeta()
       171     import pdb; pdb.set_trace()
   --> 172     connections = {}
       173     for path in paths:

   (Pdb++)

For more information see https://github.com/antocuni/pdb
