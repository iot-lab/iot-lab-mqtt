# -*- coding: utf-8 -*-

r"""IoT-LAB MQTT Serial agent
============================

.. |line|             replace::  ``{serialagenttopic}/{archi}/{num}/line``
.. |linestart|        replace::  |line|\ ``/start``
.. |raw|              replace::  ``{serialagenttopic}/{archi}/{num}/raw``
.. |rawstart|         replace::  |raw|\ ``/start``
.. |stop|             replace::  ``{serialagenttopic}/{archi}/{num}/stop``
.. |stopall|          replace::  ``{serialagenttopic}/stopall``
.. |error_t|          replace::  ``{serialagenttopic}/error``

.. |channel|          replace::  Channel
.. |request|          replace::  Request
.. |error|            replace::  Error


Serial agent provide access to the nodes serial link.
The serial redirection should first be started for each node in a mode.


Serial agent base topic: ::

   {prefix}/iot-lab/serial/{site}/

Every topics from serial agent topics start by this topic prefix

:param prefix: configured prefix
:param site: site where the agent is run


Topics Summary
==============

+------------------------+----------+-----------------------------------------+
| Name                   | Type     | Topic                                   |
+========================+==========+=========================================+
| Line redirection       ||channel| | |line|                                  |
+------------------------+----------+-----------------------------------------+
| Line redirection start ||request| | |linestart|                             |
+------------------------+----------+-----------------------------------------+
| RAW redirection        ||channel| | |raw|                                   |
+------------------------+----------+-----------------------------------------+
| RAW redirection start  ||request| | |rawstart|                              |
+------------------------+----------+-----------------------------------------+
| Stop redirection       ||request| | |stop|                                  |
+------------------------+----------+-----------------------------------------+
| Stop all redirections  ||request| | |stopall|                               |
+------------------------+----------+-----------------------------------------+
| Error topic            | |error|  | |error_t|                               |
+------------------------+----------+-----------------------------------------+


Requests topics
===============

Requests allow configuring the serial agent.

Requests Format
---------------

.. Note: This may be a reference to other page

Requests are performed by sending an empty message to the ``request`` topic and
the request result is sent to ``response`` topic. Empty message on success and
error string on failure.


Start redirection in *line* mode
--------------------------------

Start one node serial redirection in *line* mode.

+-----------------------------------------------------------------------------+
| ``line/start`` request:                                                     |
+=============================================================================+
| Topic:                                                                      |
|                                                                             |
|    |linestart|                                                              |
|                                                                             |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | *{topic}*/{clientid}/{requestid}        | *empty*              |
+------------+-----------------------------------------+----------------------+
| Response   | *{topic}*/{clientid}/{requestid}/**ret**| *empty* or error_msg |
+------------+-----------------------------------------+----------------------+



Start redirection in *raw* mode
-------------------------------

.. Note:: RAW redirection not implemented for the moment

Start one node serial redirection in *raw* mode.

+-----------------------------------------------------------------------------+
| ``raw/start`` request:                                                      |
+=============================================================================+
| Topic:                                                                      |
|                                                                             |
|    |rawstart|                                                               |
|                                                                             |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | *{topic}*/{clientid}/{requestid}        | *empty*              |
+------------+-----------------------------------------+----------------------+
| Response   | *{topic}*/{clientid}/{requestid}/**ret**| *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Stop redirection
----------------

Stop one node serial redirection whatever the mode was.


+-----------------------------------------------------------------------------+
| ``stop`` request:                                                           |
+=============================================================================+
| Topic:                                                                      |
|                                                                             |
|    |stop|                                                                   |
|                                                                             |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | *{topic}*/{clientid}/{requestid}        | *empty*              |
+------------+-----------------------------------------+----------------------+
| Response   | *{topic}*/{clientid}/{requestid}/**ret**| *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Stop all redirections
---------------------

Stop all started serial redirections.

+-----------------------------------------------------------------------------+
| ``stopall`` request:                                                        |
|                                                                             |
+=============================================================================+
| Topic:                                                                      |
|                                                                             |
|    |stopall|                                                                |
|                                                                             |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | *{topic}*/{clientid}/{requestid}        | *empty*              |
+------------+-----------------------------------------+----------------------+
| Response   | *{topic}*/{clientid}/{requestid}/**ret**| *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Serial redirection topics
=========================

Text redirection
----------------

Serial redirection handling utf-8 text lines with newline characters
removed (``\n``).

One message is received per line, and when sending a message, the newline
character is automatically added.

+-----------------------------------------------------------------------------+
| **Text line serial redirection**                                            |
+=============================================================================+
| Topic:                                                                      |
|                                                                             |
|   |line|                                                                    |
|                                                                             |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Read       | *{topic}*                               | UTF-8 text line      |
+------------+-----------------------------------------+----------------------+
| Write      | *{topic}*/**write**                     | UTF-8 text line      |
+------------+-----------------------------------------+----------------------+


RAW redirection
---------------

.. Note:: RAW redirection not implemented for the moment

Serial redirection handling raw data.

Group of bytes are sent when received from the node redirection.
No handling is done when receiving/sending.

+-----------------------------------------------------------------------------+
| **RAW serial redirection**                                                  |
+=============================================================================+
| Topic:                                                                      |
|                                                                             |
|   |raw|                                                                     |
|                                                                             |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Read       | *{topic}*                               | RAW bytes            |
+------------+-----------------------------------------+----------------------+
| Write      | *{topic}*/**write**                     | RAW bytes            |
+------------+-----------------------------------------+----------------------+


Error Topic
===========

Asynchronous error messages are posted to error topic.
Failure on requests are not duplicated here.

* |error_t|

+-----------------------------------------------------------------------------+
| **Serial agent error topic**                                                |
+=============================================================================+
| Topic:                                                                      |
|                                                                             |
|    |error_t|                                                                |
|                                                                             |
+----------------+------------------------------------------------------------+
| **Message**    | ::                                                         |
|                |                                                            |
|                |    relative/topic/from/serialagentttopic                   |
|                |    "error_message"                                         |
+----------------+------------------------------------------------------------+


"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
