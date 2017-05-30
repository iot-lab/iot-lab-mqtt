# -*- coding:utf-8 -*-

"""IoT-LAB MQTT Radio Sniffer agent client"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import threading

import iotlabmqtt.radiosniffer
from iotlabmqtt import common
from iotlabmqtt import mqttcommon

from . import common as clientcommon

PARSER = common.MQTTAgentArgumentParser()
clientcommon.parser_add_site_arg(PARSER)


class PcapFiles(object):
    """Handle pcap files by type.

    Wraps a dict of pcap files with an interface to allow correct management
    and data integrity. It is Thread safe.
    """
    def __init__(self):
        super().__init__()
        self.files = {}
        self._lock = threading.Lock()

    def clear(self, pcaptype):
        """Remove given file and close it."""
        with self._lock:  # pylint:disable=not-context-manager
            return self._clear(pcaptype)

    def _clear(self, pcaptype):
        try:
            self.files[pcaptype].close()
        except KeyError:
            pass
        finally:
            self.files.pop(pcaptype, None)

    def set(self, pcaptype, pcapfd, pcap_header):
        """Set pcap file as `pcaptype` and write its header."""
        with self._lock:  # pylint:disable=not-context-manager
            return self._set(pcaptype, pcapfd, pcap_header)

    def _set(self, pcaptype, pcapfd, pcap_header):
        self._clear(pcaptype)

        self.files[pcaptype] = pcapfd

        self._write(pcaptype, pcap_header)

    def write(self, pcaptype, data):
        """Write to given `pcaptype` file if its set."""
        with self._lock:  # pylint:disable=not-context-manager
            self._write(pcaptype, data)

    def _write(self, pcaptype, data):
        try:
            self.files[pcaptype].write(data)
            self.files[pcaptype].flush()
        except KeyError:
            pass


class RadioSnifferShell(clientcommon.CmdShell):
    """Radio Sniffer Agent Shell.

    :param host: broker host
    :param port: broker port
    :param prefix: topics prefix
    :param site: agent site
    """

    RAWSTART_USAGE = ('rawstart ARCHI NUM CHANNEL\n'
                      '  ARCHI:   m3/a8\n'
                      '  NUM:     node num\n'
                      '  CHANNEL: sniffer channel\n')
    RAWPCAP_USAGE = ('rawpcap FILEPATH\n'
                     '  FILEPATH: rawpcap output\n')
    RAWPCAPCLOSE_USAGE = ('rawpcapclose\n'
                          '  Close the current rawpcap file\n')

    STOP_USAGE = ('stop ARCHI NUM\n'
                  '  ARCHI: m3/a8\n'
                  '  NUM:   node num\n')

    STOPALL_USAGE = 'stopall\n'

    SERVER = iotlabmqtt.radiosniffer.MQTTRadioSnifferAggregator

    def __init__(self, client, prefix='', site=None):
        assert site is not None
        super().__init__()

        self.clientid = clientcommon.clientid('serialclient')

        staticfmt = {'site': site}
        _topics = mqttcommon.generate_topics_dict(
            self.SERVER.TOPICS, prefix, self.SERVER.AGENTTOPIC, staticfmt)

        _print_wrapper = self.async_print_handle_readlinebuff()
        error_cb = _print_wrapper(self.error_cb)
        raw_cb = _print_wrapper(self.raw_handler)
        self.topics = {
            'raw': mqttcommon.ChannelClient(_topics['noderaw'], raw_cb),
            'rawheader': mqttcommon.RequestClient(
                _topics['raw'], 'rawheader', clientid=self.clientid),
            'rawstart': mqttcommon.RequestClient(_topics['noderaw'], 'start',
                                                 clientid=self.clientid),

            'stop': mqttcommon.RequestClient(
                _topics['node'], 'stop', clientid=self.clientid),

            'stopall': mqttcommon.RequestClient(
                _topics['agenttopic'], 'stopall', clientid=self.clientid),

            'error': mqttcommon.ErrorClient(_topics['agenttopic'],
                                            callback=error_cb),
        }

        self.pcap_files = PcapFiles()
        self.client = client
        self.client.topics = list(self.topics.values())

    def error_cb(self, message, relative_topic):  # pylint:disable=no-self-use
        """Callback on 'error' topic."""
        msg = message.payload.decode('utf-8')
        print('RADIO SNIFFER ERROR: %s: %s' % (relative_topic, msg))

    @classmethod
    def from_opts_dict(cls, prefix, site, **kwargs):
        """Create class from argparse entries."""
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix=prefix, site=site)

    def do_rawpcap(self, arg):
        """Create pcap file and get RAW header."""
        try:
            pcapfd = open(arg, 'wb', buffering=0)
        except (IOError, OSError) as err:
            print('Could not open file: %s' % err)
            raise ValueError()

        topic = self.topics['rawheader']
        ret = topic.request(self.client, b'', timeout=5)

        # No error message
        header = ret

        print('Writing RAW PCAP header: %u bytes' % len(header))
        self.pcap_files.set('raw', pcapfd, header)

    def help_rawpcap(self):
        """Help rawpcap command."""
        print(self.RAWPCAP_USAGE, end='')

    # # # # # # # # #
    # rawpcapclose  #
    # # # # # # # # #
    def do_rawpcapclose(self, _):
        """Close rawpcap file."""
        self.pcap_files.clear('raw')

    def help_rawpcapclose(self):
        """Help rawpcapclose command."""
        print(self.RAWPCAPCLOSE_USAGE, end='')

    # # # #
    # raw #
    # # # #
    def raw_handler(self, message, archi, num):  # pylint:disable=no-self-use
        """Handle packets received from sniffer."""
        packet = message.payload

        message = 'PKT: len(%u)' % len(packet)
        print('raw_handler(%s-%s): %s' % (archi, num, message))

        self.pcap_files.write('raw', packet)

    def do_rawstart(self, arg):
        """Start sniffer on CHANNEL for given node: ARCHI NUM."""
        archi, num, channel = self.cmd_split(arg)
        num = int(num)
        channel = int(channel)

        self._do_rawstart(archi, num, channel)

    def _do_rawstart(self, archi, num, channel):
        topic = self.topics['rawstart']
        channel_str = str(channel).encode('utf-8')

        ret = topic.request(self.client, channel_str, timeout=5,
                            archi=archi, num=num)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_rawstart(self):
        """Help rawstart command."""
        print(self.RAWSTART_USAGE, end='')

    # # # # #
    # stop  #
    # # # # #
    def do_stop(self, arg):
        """Stop node sniffer: ARCHI NUM."""
        archi, num = self.cmd_split(arg)
        num = int(num)

        topic = self.topics['stop']
        ret = topic.request(self.client, b'', timeout=5,
                            archi=archi, num=num)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_stop(self):
        """Help stop command."""
        print(self.STOP_USAGE, end='')

    # # # # # #
    # stopall #
    # # # # # #
    def do_stopall(self, _):
        """Stop all nodes sniffer."""
        topic = self.topics['stopall']
        ret = topic.request(self.client, b'', timeout=5)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_stopall(self):
        """Help stopall command."""
        print(self.STOPALL_USAGE, end='')

    def run(self):
        """Run client and shell."""
        self.start()
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            pass
        self.stop()

    def start(self):
        """Start Agent."""
        self.client.start()

    def stop(self):
        """Stop agent."""
        self.client.stop()


def main(opts=None):
    """SerialAgent shell client.

    :param opts: If provided, don't parse command line but use it instead
    :type opts: argparse Namespace object
    """
    opts = opts or PARSER.parse_args()
    shell = RadioSnifferShell.from_opts_dict(**vars(opts))
    shell.run()
