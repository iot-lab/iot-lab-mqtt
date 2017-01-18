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
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os
import socket
import threading
import asyncore

from . import common
from . import mqttcommon

PARSER = common.MQTTAgentArgumentParser()


class RawHandler(object):  # pylint:disable=too-few-public-methods
    """Raw data handler."""
    def __init__(self, handler):
        self.handler = handler

    def __call__(self, data):
        """Call handler on raw data."""
        self.handler(data)


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


class Connection(asyncore.dispatcher_with_send):
    """
    Handle the connection to one node
    Data is managed with asyncore. So to work asyncore.loop() should be run.

    Child class should re-implement 'handle_data'
    """

    PORT = 20000
    RECV_LEN = 8192

    def __init__(self, archi, num, event_handler, data_handler=None):
        asyncore.dispatcher_with_send.__init__(self)

        self.address = self._address(archi, num)

        self.event_handler = event_handler
        self.data_handler = data_handler

    def _address(self, archi, num):
        """Return socket address for archi/num.

        Hack for 'localhost' to use ``self.num`` as port.
        """
        if archi == 'localhost':
            return archi, int(num)
        else:
            return ('node-%s-%s' % (archi, num), self.PORT)

    def handle_data(self, data):
        """Call given data_handler."""
        if self.data_handler:
            self.data_handler(data)

    def start(self):
        """Connects to node serial port:"""
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.connect(self.address)
        except (IOError, OverflowError):
            self.handle_close()

    def handle_connect(self):
        """Node connected."""
        self.event_handler('connect')

    def handle_close(self):
        """Close the connection and clear buffer."""
        self.close()
        self.event_handler('close')

    def handle_read(self):
        """Read bytes and run data handler."""
        data = self.recv(self.RECV_LEN)
        self.handle_data(data)

    def handle_error(self):
        """Error."""
        self.event_handler('error')


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

    def __init__(self, archi, num, closed_cb, error_cb):
        self.host = self.hostname(archi, num)
        self.closed_cb = closed_cb
        self.error_cb = error_cb

        self.state = 'closed'
        self.reply_publisher = None
        self.connection = Connection(archi, num, self.conn_event_handler)

        self._lock = threading.Lock()

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

    @common.synchronized('_lock')
    def close(self):
        """Close connection and state."""
        self._close()
        return b''  # in case of a request

    def _close(self):
        """Set 'closed' state, resets data_handler and call ``closed_cb``."""
        previous_state = self.state
        try:
            self.connection.close()
            self.connection.data_handler = None
        except AttributeError:
            pass
        self.state = 'closed'
        self.closed_cb(self)
        return previous_state

    @common.synchronized('_lock')
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
        else:
            raise ValueError('Got connect event in invalid state')

    def _event_error(self):
        error = common.traceback_error()
        previous_state = self._close()

        if previous_state == 'linestarting':
            self._reply_request('Connection failed: %s' % error)

        else:
            self.error_cb(self, error)

    def _event_close(self):
        error = 'Connection closed'
        previous_state = self._close()

        if previous_state == 'linestarting':
            self._reply_request(error)

        elif previous_state == 'line':
            raise ValueError(error)

        else:
            assert self.state == 'closed'

    @common.synchronized('_lock')
    def req_linestart(self, reply_publisher, line_handler):
        """Request to start line."""

        if self.state == 'line':
            return b''

        if self.state == 'linestarting':
            err = "Already executing 'linestart'. Wait or stop it first"
            return err.encode('utf-8')

        assert self.state == 'closed'

        # Start line mode and register 'line_handler'
        self.state = 'linestarting'
        self.connection.data_handler = line_handler

        # Async answer
        self.reply_publisher = reply_publisher
        self.connection.start()
        return None

    @common.synchronized('_lock')
    def lineinput(self, payload):
        """Send ``payload`` with a newline to the node connection."""
        if self.state != 'line':
            raise ValueError("lineinput while not in 'line' mode")

        line = payload + b'\n'
        self.connection.send(line)


class MQTTAggregator(object):
    """Aggregator implementation for MQTT."""

    ASYNCORE_LOOP_KWARGS = {'timeout': 1, 'use_poll': True}

    PREFIX = 'iot-lab/serial/{site}'
    TOPICS = {
        'prefix': PREFIX,
        'node': os.path.join(PREFIX, '{archi}/{num}'),
        'line': os.path.join(PREFIX, '{archi}/{num}/line'),
    }

    HOSTNAME = os.uname()[1]

    def __init__(self, host, port=None, prefix=''):
        super().__init__()

        staticfmt = {'site': self.HOSTNAME}
        _topics = mqttcommon.format_topics_dict(self.TOPICS, prefix, staticfmt)

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
                _topics['prefix'], 'stopall', callback=self.cb_stopall),

            'error': mqttcommon.ErrorServer(_topics['prefix']),
        }

        self.nodes = {}
        self.keep_alive = None
        self.thread = threading.Thread(target=self._loop)

        self.client = mqttcommon.MQTTClient(host, port=port,
                                            topics=self.topics)

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
        new_node = Node(archi, num, self._node_closed_cb, self._node_error)
        node = self.nodes.setdefault(Node.hostname(archi, num), new_node)

        line_handler = self._line_handler(archi, num)
        return node.req_linestart(message.reply_publisher, line_handler)

    def _line_handler(self, archi, num):
        """Line handler for node ``archi``, ``num``.

        Publish the message to the correct topic for ``archi``, ``num``.
        """
        channel = self.topics['line']
        publisher = channel.output_publisher(self.client, archi, num)
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
        self.keep_alive = common.keep_alive_dispatcher()
        self.thread.start()
        self.client.start()

    def _loop(self):
        """Run asyncore loop."""
        return asyncore.loop(**self.ASYNCORE_LOOP_KWARGS)

    def stop(self):
        """Stop agent."""
        self.client.stop()
        self._stop_all_nodes()
        self.keep_alive.close()
        self.thread.join()

    def _stop_all_nodes(self):
        """Close all nodes connections."""
        for node in list(self.nodes.values()):
            node.close()


def main():
    """Run serial agent."""
    opts = PARSER.parse_args()
    aggr = MQTTAggregator(opts.broker, port=opts.broker_port,
                          prefix=opts.prefix)
    aggr.run()


if __name__ == '__main__':
    main()
