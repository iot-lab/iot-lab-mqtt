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

import os
import threading
import tempfile
import contextlib

from . import common
from . import iotlabapi
from . import mqttcommon

PARSER = common.MQTTAgentArgumentParser()
iotlabapi.parser_add_iotlabapi_args(PARSER)


@contextlib.contextmanager
def _firmware_file(data):
    """Context manager that yields a temporary file with ``data``."""
    sha1_suffix = '--sha1:%s' % common.short_hash(data)

    with tempfile.NamedTemporaryFile('w+b', suffix=sha1_suffix) as tmpfile:
        tmpfile.write(data)
        # Ensure file is flushed as it should be readable before close
        tmpfile.flush()
        yield tmpfile.name


class MQTTNodeAgent(object):
    """Node Agent implementation for MQTT."""
    AGENTTOPIC = 'iot-lab/node/{site}'
    TOPICS = {
        'node': '{archi}/{num}',
    }
    HOSTNAME = common.hostname()

    def __init__(self, client, prefix='', iotlab_api=None):
        assert iotlab_api
        super().__init__()

        staticfmt = {'site': self.HOSTNAME}
        _topics = mqttcommon.generate_topics_dict(self.TOPICS, prefix,
                                                  self.AGENTTOPIC, staticfmt)

        self.topics = {
            'reset': mqttcommon.RequestServer(_topics['node'], 'reset',
                                              callback=self.cb_reset),
            'update': mqttcommon.RequestServer(_topics['node'], 'update',
                                               callback=self.cb_update),
            'poweron': mqttcommon.RequestServer(_topics['node'], 'poweron',
                                                callback=self.cb_poweron),
            'poweroff': mqttcommon.RequestServer(_topics['node'], 'poweroff',
                                                 callback=self.cb_poweroff),

            'error': mqttcommon.ErrorServer(_topics['agenttopic']),
        }

        self.iotlabapi = iotlab_api

        self.client = client
        self.client.topics = list(self.topics.values())

    def cb_reset(self, message, archi, num):
        """Reset node cpu."""
        args = (self.iotlabapi.reset, message.reply_publisher, archi, num)
        threading.Thread(target=self._thread_command, args=args).start()
        return None

    def cb_update(self, message, archi, num):
        """Update node firmware."""
        args = (message.payload, message.reply_publisher, archi, num)
        threading.Thread(target=self._thread_update, args=args).start()
        return None

    def _thread_update(self, firmware, reply_publisher, archi, num):
        if not firmware:
            if archi != 'm3':
                err = 'Idle firmware not handled for %s' % archi
                reply_publisher(err.encode('utf-8'))
                return
            firmware = self._idle_m3_firmware()

        with _firmware_file(firmware) as firmware_path:
            ret_dict = self.iotlabapi.update(firmware_path, archi, num)

        ret = ret_dict[str(num)]
        reply_publisher(ret.encode('utf-8'))

    @staticmethod
    def _idle_m3_firmware():
        """Return m3 idle firmware."""
        path = os.path.join(os.path.dirname(__file__), 'static', 'idle_m3.elf')
        with open(path, 'rb') as firmware:
            return firmware.read()

    def cb_poweron(self, message, archi, num):
        """Power ON node."""
        args = (self.iotlabapi.poweron, message.reply_publisher, archi, num)
        threading.Thread(target=self._thread_command, args=args).start()
        return None

    def cb_poweroff(self, message, archi, num):
        """Power OFF node."""
        args = (self.iotlabapi.poweroff, message.reply_publisher, archi, num)
        threading.Thread(target=self._thread_command, args=args).start()
        return None

    @staticmethod
    def _thread_command(func, reply_publisher, archi, num):
        ret_dict = func(archi, num)
        ret = ret_dict[str(num)]
        reply_publisher(ret.encode('utf-8'))

    # Agent running

    def run(self):
        """Run agent."""
        try:
            self.start()
            common.wait_sigint()
        finally:
            self.stop()

    def start(self):
        """Start Agent."""
        self.client.start()

    def stop(self):
        """Stop agent."""
        self.client.stop()

    @classmethod
    def from_opts_dict(cls, prefix, **kwargs):
        """Create class from argparse entries."""
        api = iotlabapi.IoTLABAPI.from_opts_dict(**kwargs)
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix, iotlab_api=api)


def main():
    """Run radio sniffer agent."""
    opts = PARSER.parse_args()
    aggr = MQTTNodeAgent.from_opts_dict(**vars(opts))
    aggr.run()
