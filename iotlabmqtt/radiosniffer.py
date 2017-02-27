# -*- coding: utf-8 -*-

r"""IoT-LAB MQTT Radio Sniffer agent
====================================

Radio Sniffer Agent provide access to the IoT-LAB nodes radio sniffer.
Packets are encapsulated as ``pcap`` (`wireshark:pcap`_).

.. _wireshark\:pcap: https://wiki.wireshark.org/Development/LibpcapFileFormat

Radio Sniffer agent base topic: ::

   {prefix}/iot-lab/radiosniffer/{site}

Every topics from radio sniffer agent topics start by this topic prefix

:param prefix: configured prefix
:param site: site where the agent is run


Topics Summary
==============

.. |node|             replace::  ``{snifferagenttopic}/{archi}/{num}``
.. |rawheader|        replace::  ``{snifferagenttopic}/raw/ctl/header``
.. |raw|              replace::  |node|\ ``/raw``
.. |rawchannel|       replace::  |node|\ ``/raw/data``
.. |rawstart|         replace::  |node|\ ``/raw/ctl/start``
.. |rawstop|          replace::  |node|\ ``/raw/ctl/stop``
.. |stop|             replace::  |node|\ ``/ctl/stop``
.. |stopall|          replace::  ``{snifferagenttopic}/ctl/stopall``
.. |error_t|          replace::  ``{snifferagenttopic}/error/``

.. |channel|          replace::  :ref:`Channel <ChannelTopic>`
.. |request|          replace::  :ref:`Request <RequestTopic>`
.. |error|            replace::  :ref:`Error <ErrorTopic>`

.. |request_topic|    replace::  *{topic}*/**request/{clientid}/{requestid}**
.. |reply_topic|      replace::  *{topic}*/**reply/{clientid}/{requestid}**
.. |in_topic|         replace::  *{topic}*/**in**
.. |out_topic|        replace::  *{topic}*/**out**

+-+---------------------------------------------------------------+-----------+
| |Topic                                                          | Type      |
+=+===============================================================+===========+
|  **Radio sniffer agent**                                                    |
+-+---------------------------------------------------------------+-----------+
| ``{prefix}/iot-lab/radiosniffer/{site}``                                    |
+-+---------------------------------------------------------------+-----------+
| ||error_t|                                                      | |error|   |
+-+---------------------------------------------------------------+-----------+
| ||stopall|                                                      ||request|  |
+-+---------------------------------------------------------------+-----------+
|  **Node**                                                                   |
+-+---------------------------------------------------------------+-----------+
| ||stop|                                                         ||request|  |
+-+---------------------------------------------------------------+-----------+
|  **Raw packet sniffer**                                                     |
+-+---------------------------------------------------------------+-----------+
| ||rawheader|                                                    ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||rawstart|                                                     ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||rawstop|                                                      ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||rawchannel|                                                   || Output   |
| |                                                               || |channel||
+-+---------------------------------------------------------------+-----------+


Radio sniffer Agent global topics
=================================

Error Topic
-----------

Asynchronous error messages are posted to error topic.
Failure on requests are not duplicated here.

* |error_t|


For format see: :ref:`ErrorTopic`


Stop all redirections
---------------------

Stop all started sniffer.

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

.. _stop_sniffer:

Stop sniffer
------------

Stop given node sniffer.


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


Raw packet sniffer
==================

Topics to access to the node sniffer in `raw` packet mode.
Sniffer listen to all radio packets on a given ``channel``.

It must first be started in ``raw`` mode to have the raw packet output.

Global pcap header must be queried independently first.

:param channel: 802.15.4 channel between 11 and 26

Start sniffer in *raw* mode
---------------------------

Start one node sniffer in *raw* mode on given ``channel``.

+-----------------------------------------------------------------------------+
| ``raw/start`` request:                                                      |
+============+================================================================+
| Topic:     |    |rawstart|                                                  |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | ``Channel string``   |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Stop raw sniffer
----------------

Equivalent to :ref:`stop_sniffer` adde here for completeness

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

RAW packet sniffer PCAP global header
-------------------------------------

PCAP format consists of two main parts, a global header, then messages with a
per message header: `wireshark:pcap`_

This request returns the global header for ``raw`` mode.


+-----------------------------------------------------------------------------+
| ``raw/header`` request:                                                     |
+============+================================================================+
| Topic:     |    |rawheader|                                                 |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | `Global pcap header` |
+------------+-----------------------------------------+----------------------+


Raw packet sniffer
------------------

Sniffer sends 802.15.4 raw radio frames encapsulated as ``pcap``.

One sniffed packet is sent by message. PCAP payload format is::

   Packet PCAP Header | Packet data

PCAP Header contains: ::

   :4 bytes: Timestamp seconds
   :4 bytes: Timestamp microseconds
   :4 bytes: Number of octet saved
   :4 bytes: Actual lengt of packet


+-----------------------------------------------------------------------------+
| **802.15.4 RAW sniffer channel**                                            |
+============+================================================================+
| Topic:     |    |rawchannel|                                                |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Output     | |out_topic|                             | PCAP packet          |
+------------+-----------------------------------------+----------------------+
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622
