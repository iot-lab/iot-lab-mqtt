# -*- coding: utf-8 -*-

"""IoT-LAB MQTT Serial agent client"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import iotlabmqtt.serial
from iotlabmqtt import common
from iotlabmqtt import mqttcommon

from . import common as clientcommon


PARSER = common.MQTTAgentArgumentParser()
clientcommon.parser_add_site_arg(PARSER)


class SerialShell(clientcommon.CmdShell):
    """Serial Agent Shell.

    :param client: mqttclient instance
    :param prefix: topics prefix
    :param site: agent site
    """
    LINESTART_USAGE = ('linestart ARCHI NUM\n'
                       '  ARCHI: m3/a8\n'
                       '  NUM:   node num\n')
    LINEWRITE_USAGE = ('linewrite ARCHI NUM MESSAGE\n'
                       '  ARCHI: m3/a8\n'
                       '  NUM:   node num\n'
                       '  MESSAGE: Message line to send\n')
    STOP_USAGE = ('stop ARCHI NUM\n'
                  '  ARCHI: m3/a8\n'
                  '  NUM:   node num\n')

    STOPALL_USAGE = 'stopall\n'

    SERVER = iotlabmqtt.serial.MQTTAggregator

    def __init__(self, client, prefix, site=None):
        assert site is not None
        super().__init__()

        self.clientid = clientcommon.clientid('serialclient')

        staticfmt = {'site': site}
        _topics = mqttcommon.generate_topics_dict(
            self.SERVER.TOPICS, prefix, self.SERVER.AGENTTOPIC, staticfmt)

        _print_wrapper = self.async_print_handle_readlinebuff()
        line_cb = _print_wrapper(self.line_handler)
        error_cb = _print_wrapper(self.error_cb)

        self.topics = {
            'line': mqttcommon.ChannelClient(_topics['line'], line_cb),
            'linestart': mqttcommon.RequestClient(
                _topics['line'], 'start', clientid=self.clientid),
            'linestop': mqttcommon.RequestClient(
                _topics['line'], 'stop', clientid=self.clientid),

            'stop': mqttcommon.RequestClient(
                _topics['node'], 'stop', clientid=self.clientid),

            'stopall': mqttcommon.RequestClient(
                _topics['agenttopic'], 'stopall', clientid=self.clientid),

            'error': mqttcommon.ErrorClient(_topics['agenttopic'],
                                            callback=error_cb),
        }

        self.client = client
        self.client.topics = list(self.topics.values())

    def error_cb(self, message, relative_topic):  # pylint:disable=no-self-use
        """Callback on 'error' topic."""
        msg = message.payload.decode('utf-8')
        print('SERIAL ERROR: %s: %s' % (relative_topic, msg))

    @classmethod
    def from_opts_dict(cls, prefix, site, **kwargs):
        """Create class from argparse entries."""
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix=prefix, site=site)

    # # # # #
    # line  #
    # # # # #
    def line_handler(self, message, archi, num):  # pylint:disable=no-self-use
        """Handle line received from nodes."""
        line = message.payload.decode('utf-8', 'replace')
        print('line_handler(%s-%s): %s' % (archi, num, line))

    # # # # # # #
    # linestart #
    # # # # # # #
    def do_linestart(self, arg):
        """Start line mode to given node: ARCHI NUM"""
        archi, num = self.cmd_split(arg)
        num = int(num)

        self._do_linestart(archi, num)

    def _do_linestart(self, archi, num):
        topic = self.topics['linestart']

        ret = topic.request(self.client, b'', timeout=5,
                            archi=archi, num=num)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_linestart(self):
        """Help linestart command."""
        print(self.LINESTART_USAGE, end='')

    # # # # # # #
    # linewrite #
    # # # # # # #
    def do_linewrite(self, arg):
        """Write line to given node: ARCHI NUM MESSAGE."""
        archi, num, message = self.cmd_split(arg, 2)
        num = int(num)

        payload = message.encode('utf-8')
        self.topics['line'].send(self.client, payload, archi=archi, num=num)

    def help_linewrite(self):
        """Help linewrite command."""
        print(self.LINEWRITE_USAGE, end='')

    # # # # #
    # stop  #
    # # # # #
    def do_stop(self, arg):
        """Stop node redirection: ARCHI NUM."""
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
        """Stop all nodes redirection."""
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
    shell = SerialShell.from_opts_dict(**vars(opts))
    shell.run()
