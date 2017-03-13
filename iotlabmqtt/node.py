# -*- coding: utf-8 -*-

r"""IoT-LAB MQTT Node agent
===========================

Node Agent provides access to the IoT-LAB nodes interactions:

* update the node firmware
* reset the CPU
* power node ON and OFF

Node agent base topic: ::

   {prefix}/iot-lab/node/{site}

Every topics from node agent topics start by this topic prefix

:param prefix: configured prefix
:param site: site where the agent is run


Topics Summary
==============

.. |node|             replace::  ``{nodeagenttopic}/{archi}/{num}``

.. |update|           replace:: |node|\ ``/ctl/update``
.. |reset|            replace:: |node|\ ``/ctl/reset``
.. |poweron|          replace:: |node|\ ``/ctl/poweron``
.. |poweroff|         replace:: |node|\ ``/ctl/poweroff``
.. |error_t|          replace::  ``{nodeagenttopic}/error/``


.. |request|          replace::  :ref:`Request <RequestTopic>`
.. |error|            replace::  :ref:`Error <ErrorTopic>`

.. |request_topic|    replace::  *{topic}*/**request/{clientid}/{requestid}**
.. |reply_topic|      replace::  *{topic}*/**reply/{clientid}/{requestid}**

+-+---------------------------------------------------------------+-----------+
| |Topic                                                          | Type      |
+=+===============================================================+===========+
|  **Node agent**                                                             |
+-+---------------------------------------------------------------+-----------+
| ``{prefix}/iot-lab/node/{site}``                                            |
+-+---------------------------------------------------------------+-----------+
| ||error_t|                                                      | |error|   |
+-+---------------------------------------------------------------+-----------+
|  **Node**                                                                   |
+-+---------------------------------------------------------------+-----------+
| ||update|                                                       ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||reset|                                                        ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||poweron|                                                      ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||poweroff|                                                     ||request|  |
+-+---------------------------------------------------------------+-----------+


Node Agent global topics
========================

Error Topic
-----------

Asynchronous error messages are posted to error topic.
Failure on requests are not duplicated here.

* |error_t|


For format see: :ref:`ErrorTopic`


Node topics
===========

Requests to interact with nodes.


.. |postnotespace| raw:: html

   <p></p>

Update firmware
---------------

Update node with given firmware. If no firmware is provided ``empty``,
default ``idle`` firmware is used instead.

:archi: supported ``m3``

|postnotespace|

+-----------------------------------------------------------------------------+
| ``update`` request:                                                         |
+============+================================================================+
| Topic:     |    |update|                                                    |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         |``Firmware binary`` or|
|            |                                         | *empty* for ``idle`` |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Reset cpu
---------

Reset node CPU to restart firmware execution.

:archi: supported ``m3``

|postnotespace|

+-----------------------------------------------------------------------------+
| ``reset`` request:                                                          |
|                                                                             |
+============+================================================================+
| Topic:     |    |reset|                                                     |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Power OFF Node
--------------

Power OFF node.

:Note: Nodes are powered ON by default.
:archi: supported ``m3``, ``a8``

|postnotespace|

+-----------------------------------------------------------------------------+
| ``poweroff`` request:                                                       |
|                                                                             |
+============+================================================================+
| Topic:     |    |poweroff|                                                  |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Power ON Node
-------------

Power ON node if it has been powered OFF.
Powering ON an already powered ON does nothing.

:Note: Nodes are powered ON by default.
:archi: supported ``m3``, ``a8``

|postnotespace|

+-----------------------------------------------------------------------------+
| ``poweron`` request:                                                        |
|                                                                             |
+============+================================================================+
| Topic:     |    |poweron|                                                   |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622
