.. Copyright 2016 - 2018  Ternaris.
.. SPDX-License-Identifier: CC-BY-SA-4.0

.. _patterns:

Patterns and known issues
=========================

.. _reduce_separately:

Reduce separately
-----------------

Message are read from bag files ordered by timestamp. For every stream (topic) a limited amount of messages is kept in deques in memory. Nodes consuming only one stream are immediately served. Nodes consuming multiple streams might end up waiting for messages from a stream seeing no messages, while the deque of another stream it is subscribed to is already phasing out message the node has not pulled yet. If this happens you will see a message of the form:

.. code-block:: console

   Error: raw_messages pulled bagmeta message 0 not being in memory anymore.
   See https://ternaris.com/marv-robotics/docs/patterns.html#reduce-separately

Depending on your use case you might succeed in simply increasing the cache size:

.. code-block:: console

   marv run --cachesize 5000 ...

However, typically it is a sign of a wrongly structured node graph.

**BAD**:

.. code-block:: python

   @marv.node()
   @marv.input('stream1', marv.select(messages, '/low/frequency'))
   @marv.input('stream2', marv.select(messages, '/high/frequency'))
   def mynode(stream1, stream2):
       yield marv.set_header()

       sum1 = None
       rosmsg = get_message_type(stream1)() if stream1.msg_type else None
       while True:
           msg = yield marv.pull(stream1)
           if msg is None:
               break
           rosmsg.deserialize(msg.data)
	   sum1 += rosmsg.data

       sum2 = None
       rosmsg = get_message_type(stream2)() if stream2.msg_type else None
       while True:
           msg = yield marv.pull(stream2)
           if msg is None:
               break
           rosmsg.deserialize(msg.data)
	   sum2 += rosmsg.data

       yield marv.push({'sums': [sum1, sum2]})


**GOOD**:

.. code-block:: python

   @marv.node()
   @marv.input('stream1', marv.select(messages, '/low/frequency'))
   def sum1(stream1):
       yield marv.set_header()

       sum1 = None
       rosmsg = get_message_type(stream1)() if stream1.msg_type else None
       while True:
           msg = yield marv.pull(stream1)
           if msg is None:
               break
           rosmsg.deserialize(msg.data)
	   sum1 += rosmsg.data

       yield marv.push({'value': sum1})

   @marv.node()
   @marv.input('stream2', marv.select(messages, '/high/frequency'))
   def sum2(stream2):
       yield marv.set_header()

       sum2 = None
       rosmsg = get_message_type(stream2)() if stream2.msg_type else None
       while True:
           msg = yield marv.pull(stream2)
           if msg is None:
               break
           rosmsg.deserialize(msg.data)
	   sum2 += rosmsg.data

       yield marv.push({'value': sum2})

   @marv.node()
   @marv.input('sum1', sum1)
   @marv.input('sum2', sum2)
   def mynode(sum1, sum2):
       yield marv.set_header()

       sum1 = yield marv.pull(sum1)
       sum2 = yield marv.pull(sum2)

       yield marv.push({'sums': [sum1, sum2]})

If this does not cover your use case and you expect MARV to behave differently, please check whether there is a fitting [issue](https://github.com/ternaris/marv-robotics/issues) already. If no such issue exist, please open a new one providing a [minimal working example](https://github.com/ternaris/marv-robotics#reporting-issues--minimal-working-example).
