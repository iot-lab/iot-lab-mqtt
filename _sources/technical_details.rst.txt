Technical details
=================


Usage of topics
---------------

Topics are a one way packet transport system. This will imply some design
constraints.

Error topic
^^^^^^^^^^^

As not all the following communication mechanisms have a response, communicating
errors or failures should happen on a dedicated error topic.

Two way streams
^^^^^^^^^^^^^^^

Two way stream require having one topic for one side and one for the other.
This includes serial port forwarding where one topic is used to read and one to
write.

Request model
^^^^^^^^^^^^^

Requests is a form of two way stream, however, a response must correspond to the
right request. For this, per request topic should be used.
The chosen format is the following:

::

   # Request topic
   {prefix}/topic/for/request/{client_id}/{request_id}
   # Response topic
   {prefix}/topic/for/request/{client_id}/{request_id}/ret

In practice, using topic wildcard topic subscribe, only one subscribe is
necessary per agent/client/request: ::

   # Agent subscribe
   {prefix}/topic/for/request/+/+
   # Client subscribe
   {prefix}/topic/for/request/{client_id}/+/ret

For ``client_id`` I recommend using a readable identifier concatenated to an
UUID to ensure both readability and uniqueness.


Sending both UTF-8 and binary in a message
------------------------------------------

In the case of firmware update, the message will need to contain both a list of
nodes and a firmware binary. It has been chosen to separate the UTF-8 string
from the binary payload using ``0xFF`` byte.

::

   <UTF-8 encoded JSON string> 0xFF <Binary data>

In fact, ``0xFF`` is never used in a UTF-8 encoded string `wikipedia:utf-8`_
so the payload can safely be split of the first occurence of ``0xFF`` without
requiring to try decoding the string.

.. _wikipedia\:utf-8: https://en.wikipedia.org/wiki/UTF-8#Advantages_2
