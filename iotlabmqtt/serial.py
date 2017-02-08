# -*- coding: utf-8 -*-

r"""IoT-LAB MQTT Serial agent
============================

.. |node|             replace::  ``{serialagenttopic}/{archi}/{num}``
.. |line|             replace::  |node|\ ``/line``
.. |linechannel|      replace::  |node|\ ``/line/data``
.. |linestart|        replace::  |node|\ ``/line/ctl/start``
.. |linestop|         replace::  |node|\ ``/line/ctl/stop``
.. |raw|              replace::  |node|\ ``/raw``
.. |rawchannel|       replace::  |node|\ ``/raw/data``
.. |rawstart|         replace::  |node|\ ``/raw/ctl/start``
.. |rawstop|          replace::  |node|\ ``/raw/ctl/stop``
.. |stop|             replace::  |node|\ ``/ctl/stop``
.. |stopall|          replace::  ``{serialagenttopic}/ctl/stopall``
.. |error_t|          replace::  ``{serialagenttopic}/error/``

.. |channel|          replace::  :ref:`Channel <ChannelTopic>`
.. |request|          replace::  :ref:`Request <RequestTopic>`
.. |error|            replace::  :ref:`Error <ErrorTopic>`

.. |request_topic|    replace::  *{topic}*/**request/{clientid}/{requestid}**
.. |reply_topic|      replace::  *{topic}*/**reply/{clientid}/{requestid}**
.. |in_topic|         replace::  *{topic}*/**in**
.. |out_topic|        replace::  *{topic}*/**out**


Serial agent provide access to the nodes serial link.
The serial redirection should first be started for each node in a mode.


Serial agent base topic: ::

   {prefix}/iot-lab/serial/{site}

Every topics from serial agent topics start by this topic prefix

:param prefix: configured prefix
:param site: site where the agent is run


Topics Summary
==============

+-+----------------------------------------------------------------+----------+
| |Topic                                                           | Type     |
+=+================================================================+==========+
|  **Serial agent**                                                           |
+-+----------------------------------------------------------------+----------+
| ``{prefix}/iot-lab/serial/{site}``                                          |
+-+----------------------------------------------------------------+----------+
| ||error_t|                                                       | |error|  |
+-+----------------------------------------------------------------+----------+
| ||stopall|                                                       ||request| |
+-+----------------------------------------------------------------+----------+
|  **Node**                                                                   |
+-+----------------------------------------------------------------+----------+
| ||stop|                                                          ||request| |
+-+----------------------------------------------------------------+----------+
|  **Line redirection**                                                       |
+-+----------------------------------------------------------------+----------+
| ||linestart|                                                     ||request| |
+-+----------------------------------------------------------------+----------+
| ||linestop|                                                      ||request| |
+-+----------------------------------------------------------------+----------+
| ||linechannel|                                                   ||channel| |
+-+----------------------------------------------------------------+----------+
|  **Raw redirection**                                                        |
+-+----------------------------------------------------------------+----------+
| ||rawstart|                                                      ||request| |
+-+----------------------------------------------------------------+----------+
| ||rawstop|                                                       ||request| |
+-+----------------------------------------------------------------+----------+
| ||rawchannel|                                                    ||channel| |
+-+----------------------------------------------------------------+----------+


Serial Agent global topics
==========================

Error Topic
-----------

Asynchronous error messages are posted to error topic.
Failure on requests are not duplicated here.

* |error_t|


For format see: :ref:`ErrorTopic`


Stop all redirections
---------------------

Stop all started serial redirections.

+-----------------------------------------------------------------------------+
| ``stopall`` request:                                                        |
|                                                                             |
+============+================================================================+
| Topic:     |    |stopall|                                                   |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Node topics
===========

.. _stop_redirection:

Stop redirection
----------------

Stop given node serial redirection whatever the mode was.


+-----------------------------------------------------------------------------+
| ``stop`` request:                                                           |
+============+================================================================+
| Topic:     |    |stop|                                                      |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Line redirection topics
=======================

Topics to access to the node serial port redirection in 'line' mode.
The redirection must first be started in ``line`` mode to have the line output.


Data received from the node is split on newlines characters with newlines
stripped.

As newlines characters are not used in multibytes ``utf-8`` characters,
each line remains, if it was, a valid ``utf-8`` string.
On invalid ``utf-8`` strings sent by the node,
the data will also be invalid in the topic.


Start redirection in *line* mode
--------------------------------

Start one node serial redirection in *line* mode.

+-----------------------------------------------------------------------------+
| ``line/start`` request:                                                     |
+============+================================================================+
| Topic:     |    |linestart|                                                 |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Stop line redirection
---------------------

Equivalent to :ref:`stop_redirection` added here for completeness.

+-----------------------------------------------------------------------------+
| ``line/stop`` request:                                                      |
+============+================================================================+
| Topic:     |    |linestop|                                                  |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Line redirection
----------------

Serial redirection sends text lines with newline characters removed (``\n``).

One message is received per line, and when sending a message, the newline
character is automatically added.

+-----------------------------------------------------------------------------+
| **Text line serial redirection**                                            |
+============+================================================================+
| Topic:     |    |linechannel|                                               |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Output     | |out_topic|                             | UTF-8 text line      |
+------------+-----------------------------------------+----------------------+
| Input      | |in_topic|                              | UTF-8 text line      |
+------------+-----------------------------------------+----------------------+


Raw redirection topics
======================

.. Note:: RAW redirection not implemented for the moment

Start redirection in *raw* mode
-------------------------------

Start one node serial redirection in *raw* mode.

+-----------------------------------------------------------------------------+
| ``raw/start`` request:                                                      |
+============+================================================================+
| Topic:     |    |rawstart|                                                  |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+

Stop raw redirection
--------------------

Equivalent to :ref:`stop_redirection` added here for completeness.

+-----------------------------------------------------------------------------+
| ``raw/stop`` request:                                                       |
+============+================================================================+
| Topic:     |    |rawstop|                                                   |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


RAW redirection
---------------

.. Note:: RAW redirection not implemented for the moment

Serial redirection handling raw data.

Group of bytes are sent when received from the node redirection.
No handling is done when receiving/sending.

+-----------------------------------------------------------------------------+
| **RAW serial redirection**                                                  |
+============+================================================================+
| Topic:     |    |rawchannel|                                                |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Output     | |out_topic|                             | RAW bytes            |
+------------+-----------------------------------------+----------------------+
| Input      | |in_topic|                              | RAW bytes            |
+------------+-----------------------------------------+----------------------+
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
