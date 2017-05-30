# -*- coding: utf-8 -*-

r"""IoT-LAB MQTT Radio Sniffer agent
====================================

Radio Sniffer Agent provides access to the IoT-LAB nodes radio sniffer.
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

import struct
import threading

from . import common
from . import iotlabapi
from . import mqttcommon
from . import asyncconnection

PARSER = common.MQTTAgentArgumentParser()
iotlabapi.parser_add_iotlabapi_args(PARSER)


class ZepToPcap(object):  # pylint:disable=too-few-public-methods
    """Zep to Pcap converter.

    On ``convert`` converts the message as a zep packet.
    """
    ZEP_PORT = 17754
    ZEP_HDR_LEN = 32
    ZEP_TIME_IDX = 9
    # http://www.tcpdump.org/linktypes.html

    LINKTYPE_ETHERNET = 1
    LINKTYPE_IEEE802_15_4 = 195  # with FCS

    # 1970 - 1900 in seconds
    NTP_JAN_1970 = 2208988800
    NTP_SECONDS_FRAC = 1 << 32

    # Network headers as network endian
    ETH_HDR = struct.pack(b'!3H3HH',
                          0, 0, 0,  # dst mac addr
                          0, 0, 0,  # src mac addr
                          0x0800)   # Protocol: (0x0800 == IP)

    LINKTYPES = {
        'RAW': LINKTYPE_IEEE802_15_4,
        'ZEP': LINKTYPE_ETHERNET,
    }

    def __init__(self, mode='RAW'):
        # configure "raw" mode
        # On raw, use linktype 802.15_4 else ethernet encapsulation
        self.mode = mode
        link_type = self.LINKTYPES[mode]
        self.header = self._pcap_main_header(link_type)

        _converter = {
            'RAW': self._convert_raw,
            'ZEP': self._convert_zep,
        }
        self.convert = _converter[mode]

    @staticmethod
    def _pcap_main_header(link_type):
        """ Return the main pcap file header for `link_type`

        PCAP headers as native endian
        """
        return struct.pack(
            b'=LHHLLLL',
            0xa1b2c3d4,  # Pcap header Little Endian
            2,           # File format major revision (i.e. pcap <2>.4)
            4,           # File format minor revision (i.e. pcap 2.<4>)
            0,           # GMT to local correction: 0 if timestamps are UTC
            0,           # accuracy of timestamps -> set it to 0
            0xffff,      # packet capture limit -> typically 65535
            link_type,   # Link (Ethernet/802.15.4 FCS/...)
        )

    @classmethod
    def _convert_raw(cls, packet):
        """ Only write the ZEP payload as pcap"""
        timestamp = cls._timestamp(packet)

        # extract payload from zep encapsulated data
        payload = packet[cls.ZEP_HDR_LEN:]

        # Only add pcap header
        length = len(payload)
        pcap_hdr = cls._pcap_header(length, timestamp[0], timestamp[1])
        length += len(pcap_hdr)

        # Actually write the data
        pcap = b''.join((pcap_hdr, payload))
        return pcap

    @classmethod
    def _convert_zep(cls, packet):
        """ Encapsulate ZEP data in pcap outfile """
        timestamp = cls._timestamp(packet)

        # Calculate all headers
        length = len(packet)

        udp_hdr = cls._udp_header(length)
        length += len(udp_hdr)

        ip_hdr = cls._ip_header(length)
        length += len(ip_hdr)

        eth_hdr = cls._eth_header(length)
        length += len(eth_hdr)

        pcap_hdr = cls._pcap_header(length, timestamp[0], timestamp[1])
        length += len(pcap_hdr)

        pcap = b''.join((pcap_hdr, eth_hdr, ip_hdr, udp_hdr, packet))
        return pcap

    @classmethod
    def _timestamp(cls, packet):
        """ Extract packet timestamp as an unix time tuple (s, us)
        Packet timestamp is in 'ntp' format.

        MSB are seconds stored since 1 january 1900
        LSB are fraction of seconds where 2**32 == 1 second
        """
        ntp_t = struct.unpack_from(b'!LL', packet, cls.ZEP_TIME_IDX)

        t_s = ntp_t[0] - cls.NTP_JAN_1970
        t_us = (1000000 * ntp_t[1]) // cls.NTP_SECONDS_FRAC

        return t_s, t_us

    @classmethod
    def _udp_header(cls, pkt_len):
        """ Get UDP Header

        2B - src_port: ZEP_PORT also but not required
        2B - dst_port: ZEP_PORT == 17754
        2B - length:   header + packet length
        2B - checksum: Disable == 0

        """
        hdr_struct = struct.Struct(b'!HHHH')
        udp_len = hdr_struct.size + pkt_len
        udp_hdr = hdr_struct.pack(cls.ZEP_PORT, cls.ZEP_PORT, udp_len, 0)
        return udp_hdr

    @classmethod
    def _ip_header(cls, pkt_len):
        """ Get the IP Header

        1B - Version | IHL:           0x45: [4 | 5] : [4b | 4b]
        1B - Type of Service:         0
        2B - Length:                  pkt_len + Header length
        2B - Identification:          0
        2B - Flags | Fragment offset: 0x4000: [2 | 0] : [3b | 13b]
        1B - TTL:                     0xff
        1B - Protocol:                0x11 UDP
        2B - Checksum:                calculated
        4B - Source Address:          0x7F000001 (127.0.0.1)
        4B - Destination Address:     0x7F000001 (127.0.0.1)

        """
        hdr_struct = struct.Struct(b'!BBHHHBBHLL')
        ip_len = hdr_struct.size + pkt_len

        # generate header with checksum == 0 to calculate checksum
        checksum = 0
        ip_hdr_csum = hdr_struct.pack(0x45, 0, ip_len, 0, 0x4000, 0xff, 0x11,
                                      checksum, 0x7F000001, 0x7F000001)
        checksum = cls._ip_checksum(ip_hdr_csum)

        # Generate header with correct checksum
        ip_hdr = hdr_struct.pack(0x45, 0, ip_len, 0, 0x4000, 0xff, 0x11,
                                 checksum, 0x7F000001, 0x7F000001)
        return ip_hdr

    @staticmethod
    def _ip_checksum(hdr):
        """ Calculate the ip checksum for given header """
        assert (len(hdr) % 2) == 0  # hdr has even length
        word_pack = struct.Struct(b'!H')

        # Sum all 16bits
        hdr_split = (hdr[i:i + 2] for i in range(0, len(hdr), 2))
        csum = sum((word_pack.unpack(word)[0] for word in hdr_split))

        # Reduce to 16b and save the one complement
        checksum = (csum + (csum >> 16)) & 0xFFFF ^ 0xFFFF
        return checksum

    @classmethod
    def _eth_header(cls, pkt_len):  # pylint:disable=unused-argument
        """ Return a static empty ethernet header

        6B - dst mac addr: 0
        6B - src mac addr: 0
        2B - protocol:     0x0800 (IP)
        """
        return cls.ETH_HDR

    @staticmethod
    def _pcap_header(pkt_len, t_s, t_us):
        """ Get the PCAP Header

        4B - Timestamp seconds:      current time
        4B - Timestamp microseconds: current time
        4B - Number of octet saved:  pkt_len
        4B - Actual lengt of packet: pkt_len
        """

        hdr_struct = struct.Struct(b'=LLLL')
        pcap_len = pkt_len
        pcap_hdr = hdr_struct.pack(t_s, t_us, pcap_len, pcap_len)
        return pcap_hdr


class ZEPHandler(object):  # pylint:disable=too-few-public-methods

    """ZEP data handler."""
    ZEP_HDR_LEN = 32  # zeptopcap.ZepPcap.ZEP_HDR_LEN
    ZEP_START = b'EX\2'

    def __init__(self, handler):
        self.data = b''
        self.handler = handler

    def __call__(self, input_data):
        """Call 'handler' on received data packet per packet."""
        data = self.data + input_data

        while True:
            data = self._strip_until_pkt_start(data)
            if (not data.startswith(self.ZEP_START) or
                    len(data) < self.ZEP_HDR_LEN):
                break

            # length = header length + data['len_byte']
            full_len = self.ZEP_HDR_LEN + self._payload_len(data)
            if len(data) < full_len:
                break

            # Extract packet
            pkt, data = data[:full_len], data[full_len:]
            self.handler(pkt)

        self.data = data

    def _payload_len(self, data):
        """Read 'length' byte from data.

        Length byte is byte at index ZEP_HDR_LEN -1.
        Use bytearray to be python2 and python3 compatible.
        `ord` does not work in python3.
        """
        return bytearray(data[self.ZEP_HDR_LEN - 1:self.ZEP_HDR_LEN])[0]

    @classmethod
    def _strip_until_pkt_start(cls, msg):
        """
        >>> msg = b'abcdEEEEEEEEEX\2'
        >>> b'EX\2' == ZEPHandler._strip_until_pkt_start(msg)
        True

        >>> msg = b'abcdEEEEEEEEEX\2' b'12345'
        >>> b'EX\2' b'12345' == ZEPHandler._strip_until_pkt_start(msg)
        True

        >>> msg = b'abcdEEE'
        >>> b'EE' == ZEPHandler._strip_until_pkt_start(msg)
        True

        >>> msg = b'abcdEEEa'
        >>> b'Ea' == ZEPHandler._strip_until_pkt_start(msg)
        True

        >>> msg = b'a'
        >>> b'a' == ZEPHandler._strip_until_pkt_start(msg)
        True

        """
        whole_index = msg.find(cls.ZEP_START)
        if whole_index == 0:   # is stripped
            return msg
        if whole_index != -1:  # found, strip first lines
            return msg[whole_index:]

        # not found but remove some chars from the buffer
        # at max 2 required in this case
        # might be invalid packet but keeps buffer small anymay
        return msg[-2:]


class SnifferConnection(asyncconnection.NodeConnection):
    """SnifferConnection implementation.

    Only overrides ``_address`` to adapt to the sniffer port.
    """
    PORT = 30000

    def _address(self, archi, num):  # overrides
        """Return socket address for archi/num.

        Hack for 'localhost' to use ``self.num`` as port.
        """
        # pylint:disable=no-else-return
        if archi == 'localhost':
            return archi, int(num)
        else:
            return ('%s-%s' % (archi, num), self.PORT)


class Node(object):  # pylint:disable=too-many-instance-attributes
    """Node resource managing sniffer connection, handling commands and events.

    :param archi: node architecture, or localhost
    :param num: node number
    :param closed_cb: callback for connection close
    :type closed_cb: Callable[[Node], None]
    :param error_cb: callback for asynchronous errors
    :type error_cb: Callable[[Node, str], None]
    """

    STATES = ('closed', 'startingsniffer', 'rawstarting', 'raw')
    CHANNELS = list(range(11, 26 + 1))

    def __init__(self, archi, num,  # pylint:disable=too-many-arguments
                 closed_cb, error_cb, iotlab_api, asyncoreservice=None):
        self.host = self.hostname(archi, num)
        self.closed_cb = closed_cb
        self.error_cb = error_cb

        self.channel = None
        self.iotlabapi = iotlab_api

        self.state = 'closed'
        self.reply_publisher = None
        self.connection = SnifferConnection(archi, num,
                                            self.conn_event_handler,
                                            service=asyncoreservice)

        # Required Rlock, connection socket errors calls event_handler('close')
        self._rlock = threading.RLock()

    @staticmethod
    def hostname(archi, num):
        """Return hostname for archi, num."""
        return archi, num

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
        if self.state == 'rawstarting':
            self._reply_request('', newstate='raw')
            return

        raise Exception('Got connect event in invalid state %s' % self.state)

    def _event_error(self):
        # Received other events exceptions
        error = common.traceback_error()
        previous_state = self._close()

        if previous_state == 'rawstarting':
            self._reply_request('Connection failed: %s' % error)
            return

        self.error_cb(self, error)

    def _event_close(self):
        # Jumps to event error
        raise Exception('Connection closed in state %s' % self.state)

    def _close(self):
        """Set 'closed' state, resets data_handler and call ``closed_cb``.

        Dont stop sniffer
        """
        previous_state = self.state
        self.connection.close()
        self.connection.data_handler = None
        self.state = 'closed'
        self.closed_cb(self)
        return previous_state

    @common.synchronized('_rlock')
    def req_rawstart(self, reply_publisher, zep_handler, channel):
        """Request to start sniffer redirection on ``channel``."""
        if self.state == 'raw':
            ret = 'Already started, stop before start to change channel'
            return ret.encode('utf-8')

        if self.state != 'closed':
            err = "Error: 'rawstarting' in mode %s. Wait or stop it first"
            return (err % self.state).encode('utf-8')

        self.state = 'startingsniffer'

        self.connection.data_handler = zep_handler
        self.reply_publisher = reply_publisher

        threading.Thread(target=self._thr_sniff_and_connect,
                         args=(channel,)).start()
        return None

    def _thr_sniff_and_connect(self, channel):
        # Should be run in a thread and not paho loop
        archi, num = self.host
        ret_dict = self.iotlabapi.set_sniffer_channel(channel, archi, num)

        profile_ret = ret_dict[str(num)]

        if profile_ret:
            with self._rlock:
                self.reply_publisher(profile_ret.encode('utf-8'))
                self.reply_publisher = None
                self._close()
        else:
            with self._rlock:
                self.state = 'rawstarting'
                self.connection.start()


class MQTTRadioSnifferAggregator(object):
    """Radio Sniffer Aggregator implementation for MQTT."""
    AGENTTOPIC = 'iot-lab/radiosniffer/{site}'
    TOPICS = {
        'raw': 'raw',
        'node': '{archi}/{num}',
        'noderaw': '{archi}/{num}/raw',
    }
    HOSTNAME = common.hostname()

    def __init__(self, client, prefix='', iotlab_api=None):
        assert iotlab_api
        super().__init__()

        staticfmt = {'site': self.HOSTNAME}
        _topics = mqttcommon.generate_topics_dict(self.TOPICS,
                                                  prefix, self.AGENTTOPIC,
                                                  staticfmt)

        self.topics = {
            'node': mqttcommon.NullTopic(_topics['node']),
            'rawheader': mqttcommon.RequestServer(
                _topics['raw'], 'rawheader', callback=self.cb_rawheader),

            'rawstart': mqttcommon.RequestServer(_topics['noderaw'], 'start',
                                                 callback=self.cb_rawstart),
            'rawstop': mqttcommon.RequestServer(_topics['noderaw'], 'stop',
                                                callback=self.cb_stop),
            'raw': mqttcommon.OutputChannelServer(_topics['noderaw']),

            'stop': mqttcommon.RequestServer(_topics['node'], 'stop',
                                             callback=self.cb_stop),

            'stopall': mqttcommon.RequestServer(_topics['agenttopic'],
                                                'stopall',
                                                callback=self.cb_stopall),

            'error': mqttcommon.ErrorServer(_topics['agenttopic']),
        }

        self.iotlabapi = iotlab_api
        self.nodes = {}
        self.asyncore = asyncconnection.AsyncoreService()

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

    def cb_rawstart(self, message, archi, num):
        """Start node sniffer in 'raw' mode.

        Create a new node if it does not currently exists.
        """
        try:
            channel = self._channel_from_payload(message.payload)
        except ValueError as err:
            return str(err).encode('utf-8')

        new_node = Node(archi, num, self._node_closed_cb, self._node_error,
                        self.iotlabapi, asyncoreservice=self.asyncore)
        node = self.nodes.setdefault(Node.hostname(archi, num), new_node)

        handler = self._raw_handler(archi, num)
        return node.req_rawstart(message.reply_publisher, handler, channel)

    @staticmethod
    def _channel_from_payload(payload):
        try:
            channel = int(payload.decode('utf-8'))
            if channel not in Node.CHANNELS:
                raise ValueError()
        except (TypeError, ValueError):
            raise ValueError('Invalid channel value, should be in [%s, %s]' %
                             (Node.CHANNELS[0], Node.CHANNELS[-1]))
        return channel

    def _raw_handler(self, archi, num):
        # """Raw handler for node ``archi``, ``num``.

        # Publish the message to the correct topic for ``archi``, ``num``.
        # """
        channel = self.topics['raw']
        publisher = channel.output_publisher(self.client, archi=archi, num=num)
        raw_encoder = ZepToPcap(mode='RAW').convert

        return ZEPHandler(lambda msg: publisher(raw_encoder(msg)))

    def _node_closed_cb(self, node):
        """Remove closed node."""
        self.nodes.pop(node.host, None)

    def cb_stop(self, message, archi, num):
        """Stop node redirection.

        In practice do not stop sniffer profile.
        """
        try:
            self.nodes[Node.hostname(archi, num)].close()
        except KeyError:
            pass
        return b''

    @staticmethod
    def cb_rawheader(_):
        """Return header for 'RAW' header."""
        return ZepToPcap(mode='RAW').header

    def cb_stopall(self, message):
        """Stop nodes sniffer redirection.

        In practice do not stop sniffer profile.
        """
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
        api = iotlabapi.IoTLABAPI.from_opts_dict(**kwargs)
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix, iotlab_api=api)


def main():
    """Run radio sniffer agent."""
    opts = PARSER.parse_args()
    aggr = MQTTRadioSnifferAggregator.from_opts_dict(**vars(opts))
    aggr.run()
