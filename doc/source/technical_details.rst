Technical details
#################

Topics format
*************

MQTT topics are a one way packet transport system.
More advanced communication scheme need using multiple topics with some
specific interfaces.

This section describes the different communication mechanisms used,
topic naming conventions and message format.

.. _ChannelTopic:

Channels
========

Two way stream require having one topic for one communication side and
one for the other.
This includes serial port forwarding where one topic is used to
read from the serial port and one to write to it.

:input topic: ``{resourcetopic}/data/in``
:output topic: ``{resourcetopic}/data/out``

Example
-------

For a resource at ``{prefix}/resource/1``, the channels topics will be:

::

    # Topic for writing to the resource
    {prefix}/resource/1/data/in
    # Topic where the resource writes its output
    {prefix}/resource/1/data/out


.. _RequestTopic:

Request model
=============

Requests allow executing commands on a resource is a form of two way stream,
one to do the request and one to give the result.
As a response must correspond to the right request and the right client,
a per request/client topic should be specified.

The chosen format is the following:

:request topic: ``{resourcetopic}/ctl/{command}/request/{clientid}/{requestid}``
:reply topic:   ``{resourcetopic}/ctl/{command}/reply/{clientid}/{requestid}``


In practice, by using wildcard topic subscribtion, only one subscribe is
necessary per agent/client/request/command: ::

   # Agent subscribe
   {prefix}/resource/topic/ctl/{command}/request/+/+
   # Client subscribe
   {prefix}/resource/topic/ctl/{command}/reply/{clientid}/+

For ``clientid`` I recommend using a readable identifier concatenated to an
UUID to ensure both readability and unicity.


.. _ErrorTopic:

Error topic
===========

As not all the following communication mechanisms have a response,
asynchronous errors or failures happen on an error topic.

The errors are sent to a subtopic from the agent error topic.
They are published to the concatenation of the agent error topic
and the topic where error happend relative to the agent topic:

::

   {agenttopic}/error/relative/topic/where/problem/occured

:payload: ``utf-8 encoded strings``.

Clients subscribe to errors for this agent with:

::

   {agenttopic}/error/#

Example
-------

An error in resource ``{agenttopic}/resource/1`` will be published to:

::

   {agenttopic}/error/resource/1

An error in the general agent to the will be published to:

::

   {agenttopic}/error/    # With the trailing `/`


Sending both UTF-8 and binary in a message
******************************************

If in a message, both text (e.g., a json) and a binary data need to be sent,
it has been chosen to separate the UTF-8 string from the binary payload
using one ``0xFF`` byte.

::

   <UTF-8 encoded JSON string> 0xFF <Binary data>

In fact, ``0xFF`` is never used in a UTF-8 encoded string `wikipedia:utf-8`_
so the payload can safely be split on the first occurence of ``0xFF`` without
requiring to first decode the string.

.. _wikipedia\:utf-8: https://en.wikipedia.org/wiki/UTF-8#Advantages_2
