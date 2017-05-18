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


Serial agent provides access to the nodes serial link.
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
from builtins import *  # pylint:disable=W0401,W0614,W0622

import threading

from . import common
from . import mqttcommon
from . import asyncconnection

PARSER = common.MQTTAgentArgumentParser()


class LineHandler(object):  # pylint:disable=too-few-public-methods
    """Line data handler."""
    def __init__(self, handler):
        self.data = b''
        self.handler = handler

    def __call__(self, data):
        """Call 'handler' on received data line by line."""

        # 'newline' byte never appear in multibyte unicode char
        # so it can be split without decoding
        self.data += data
        lines = self.data.splitlines(True)

        for full_line in lines:
            # strip newline using splitlines
            line = full_line.splitlines()[0]

            # last incomplete line
            if line == full_line:
                self.data = line
                return

            self.handler(line)

        self.data = b''


class SerialConnection(asyncconnection.NodeConnection):
    """Implement serial connection.

    Only overrides ``_address`` to adapt to the serial port.
    """
    PORT = 20000

    def _address(self, archi, num):  # overrides
        """Return socket address for archi/num.

        Hack for 'localhost' to use ``self.num`` as port.
        """
        # pylint:disable=no-else-return
        if archi == 'localhost':
            return archi, int(num)
        else:
            return ('node-%s-%s' % (archi, num), self.PORT)


class Node(object):  # pylint:disable=too-many-instance-attributes
    """Node resource managing connection, handling commands and events.

    :param archi: node architecture, or localhost
    :param num: node number
    :param closed_cb: callback for connection close
    :type closed_cb: Callable[[Node], None]
    :param error_cb: callback for asynchronous errors
    :type error_cb: Callable[[Node, str], None]
    """

    STATES = ('closed', 'linestarting', 'line')

    def __init__(self, archi, num,  # pylint:disable=too-many-arguments
                 closed_cb, error_cb, asyncoreservice=None):
        self.host = self.hostname(archi, num)
        self.closed_cb = closed_cb
        self.error_cb = error_cb

        self.state = 'closed'
        self.reply_publisher = None
        self.connection = SerialConnection(archi, num, self.conn_event_handler,
                                           service=asyncoreservice)

        # Required Rlock, connection socket errors calls event_handler('close')
        self._rlock = threading.RLock()

    @staticmethod
    def hostname(archi, num):
        """Return hostname for archi, num."""
        return archi, num

    @staticmethod
    def host_str(archi, num):
        """Host string."""
        return '%s-%s' % (archi, num)

    @property
    def state(self):
        """Node state."""
        return self._state

    @state.setter
    def state(self, value):
        """Node state, check ``value`` is a valid state."""
        assert value in self.STATES
        self._state = value  # pylint:disable=attribute-defined-outside-init

    def _reply_request(self, reply, newstate=None):
        """Reply current request and remove publisher.

        If ``newstate`` is provided, update current state.
        """
        self.state = newstate or self.state
        self.reply_publisher(reply.encode('utf-8'))
        self.reply_publisher = None

    @common.synchronized('_rlock')
    def close(self):
        """Close connection and state."""
        self._close()
        return b''  # in case of a request

    def _close(self):
        """Set 'closed' state, resets data_handler and call ``closed_cb``."""
        previous_state = self.state
        self.connection.close()
        self.connection.data_handler = None
        self.state = 'closed'
        self.closed_cb(self)
        return previous_state

    @common.synchronized('_rlock')
    def conn_event_handler(self, event):
        """Handler for connection events."""
        event_handler = {
            'connect': self._event_connect,
            'error': self._event_error,
            'close': self._event_close,
        }
        return event_handler[event]()

    def _event_connect(self):
        if self.state == 'linestarting':
            self._reply_request('', newstate='line')
            return

        raise Exception('Got connect event in invalid state %s' % self.state)

    def _event_error(self):
        # Received other events exceptions
        error = common.traceback_error()
        previous_state = self._close()

        if previous_state == 'linestarting':
            self._reply_request('Connection failed: %s' % error)
            return

        self.error_cb(self, error)

    def _event_close(self):
        # Jumps to event error
        raise Exception('Connection closed in state %s' % self.state)

    @common.synchronized('_rlock')
    def req_linestart(self, reply_publisher, line_handler):
        """Request to start line."""

        if self.state == 'line':
            return b''

        if self.state != 'closed':
            err = "Error: 'linestart' in mode %s. Wait or stop it first"
            return (err % self.state).encode('utf-8')

        # Start line mode and register 'line_handler'
        self.state = 'linestarting'
        self.connection.data_handler = line_handler

        # Async answer
        self.reply_publisher = reply_publisher
        self.connection.start()
        return None

    @common.synchronized('_rlock')
    def lineinput(self, payload):
        """Send ``payload`` with a newline to the node connection."""
        if self.state != 'line':
            raise ValueError("lineinput while not in 'line' mode")

        line = payload + b'\n'
        self.connection.send(line)


class MQTTAggregator(object):
    """Aggregator implementation for MQTT."""

    AGENTTOPIC = 'iot-lab/serial/{site}'
    TOPICS = {
        'node': '{archi}/{num}',
        'line': '{archi}/{num}/line',
    }

    HOSTNAME = common.hostname()

    def __init__(self, client, prefix=''):
        super().__init__()

        staticfmt = {'site': self.HOSTNAME}
        _topics = mqttcommon.generate_topics_dict(self.TOPICS, prefix,
                                                  self.AGENTTOPIC, staticfmt)

        self.nodes = {}
        self.asyncore = asyncconnection.AsyncoreService()

        self.topics = {
            'node': mqttcommon.NullTopic(_topics['node']),
            'line': mqttcommon.ChannelServer(_topics['line'],
                                             callback=self.cb_lineinput),
            'linestart': mqttcommon.RequestServer(
                _topics['line'], 'start', callback=self.cb_linestart),
            'linestop': mqttcommon.RequestServer(
                _topics['line'], 'stop', callback=self.cb_stop),

            'stop': mqttcommon.RequestServer(
                _topics['node'], 'stop', callback=self.cb_stop),

            'stopall': mqttcommon.RequestServer(
                _topics['agenttopic'], 'stopall', callback=self.cb_stopall),

            'error': mqttcommon.ErrorServer(_topics['agenttopic']),
        }

        self.client = client
        self.client.topics = list(self.topics.values())

    def error(self, topic, message):
        """Publish error that happend on topic."""
        self.topics['error'].publish_error(self.client, topic,
                                           message.encode('utf-8'))

    def _node_error(self, node, message):
        archi, num = node.host
        topic = self.topics['node'].topic.format(archi=archi, num=num)
        self.error(topic, message)

    def cb_lineinput(self, message, archi, num):
        """Write message to node."""
        host = Node.hostname(archi, num)
        try:
            self.nodes[host].lineinput(message.payload)
        except KeyError:
            self.error(message.topic, 'Non connected node {}'.format(
                Node.host_str(archi, num)))

    def cb_linestart(self, message, archi, num):
        """Start node redirection in 'line' mode.

        Create a new node if it does not currently exists.
        """
        new_node = Node(archi, num, self._node_closed_cb, self._node_error,
                        asyncoreservice=self.asyncore)
        node = self.nodes.setdefault(Node.hostname(archi, num), new_node)

        line_handler = self._line_handler(archi, num)
        return node.req_linestart(message.reply_publisher, line_handler)

    def _line_handler(self, archi, num):
        """Line handler for node ``archi``, ``num``.

        Publish the message to the correct topic for ``archi``, ``num``.
        """
        channel = self.topics['line']
        publisher = channel.output_publisher(self.client, archi=archi, num=num)
        return LineHandler(publisher)

    def _node_closed_cb(self, node):
        """Remove closed node."""
        self.nodes.pop(node.host, None)

    def cb_stop(self, message, archi, num):
        """Stop node redirection."""
        try:
            return self.nodes[Node.hostname(archi, num)].close()
        except KeyError:
            return b''

    def cb_stopall(self, message):
        """Stop nodes redirection."""
        self._stop_all_nodes()
        return b''

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
        self.asyncore.start()
        self.client.start()

    def stop(self):
        """Stop agent."""
        self.client.stop()
        self._stop_all_nodes()
        self.asyncore.stop()

    def _stop_all_nodes(self):
        """Close all nodes connections."""
        for node in list(self.nodes.values()):
            node.close()

    @classmethod
    def from_opts_dict(cls, prefix, **kwargs):
        """Create class from argparse entries."""
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix)


def main():
    """Run serial agent."""
    opts = PARSER.parse_args()
    aggr = MQTTAggregator.from_opts_dict(**vars(opts))
    aggr.run()
