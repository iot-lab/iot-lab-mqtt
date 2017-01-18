# -*- coding: utf-8 -*-

"""IoT-LAB MQTT Serial agent client"""


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import sys
import cmd
import shlex

from iotlabmqtt import common
from iotlabmqtt import mqttcommon
from iotlabmqtt import serial


PARSER = common.MQTTAgentArgumentParser()
PARSER.add_argument('--site', help='Site agent to use', required=True)


def async_print_handle_readlinebuff(cmd_obj):
    """Manages a clean readline buffer for asynchronous print.

    If there is content in readline buffer, add a newline before calling
    function and restore readline displayed string after function.
    """
    import readline
    import functools

    def _wrap(func):
        @functools.wraps(func)
        def _wrapped(*args, **kwargs):

            if readline.get_line_buffer():
                print()

            ret = func(*args, **kwargs)

            sys.stdout.write(cmd_obj.prompt)
            sys.stdout.write(readline.get_line_buffer())
            sys.stdout.flush()
            return ret

        return _wrapped
    return _wrap


class SerialShell(cmd.Cmd, object):
    """Serial Agent Shell.

    :param host: broker host
    :param port: broker port
    :param prefix: topics prefix
    :param site: serial agent site
    """
    ARCHIS = ('m3', 'a8', 'localhost')  # could use cli-tools here

    LINESTART_USAGE = ('linestart ARCHI NUM\n'
                       '  ARCHI: m3/a8\n'
                       '  NUM:   node num\n')
    LINEWRITE_USAGE = ('linewrite ARCHI NUM MESSAGE\n'
                       '  ARCHI: m3/a8\n'
                       '  NUM:   node num\n'
                       '  MESSAGE: Message line to sent\n')
    STOP_USAGE = ('stop ARCHI NUM\n'
                  '  ARCHI: m3/a8\n'
                  '  NUM:   node num\n')

    STOPALL_USAGE = 'stopall\n'

    TOPICS = {k: t for k, t in serial.MQTTAggregator.TOPICS.items()}

    def __init__(self, host, port=None, prefix='', site=None):
        assert site is not None
        cmd.Cmd.__init__(self)

        self.clientid = common.clientid('serialclient')

        staticfmt = {'site': site}
        _topics = mqttcommon.format_topics_dict(self.TOPICS, prefix, staticfmt)

        line_cb = async_print_handle_readlinebuff(self)(self.line_handler)
        error_cb = async_print_handle_readlinebuff(self)(self.error_cb)
        self.topics = {
            'line': mqttcommon.ChannelClient(_topics['line'], line_cb),
            'linestart': mqttcommon.RequestClient(
                _topics['line'], 'start', clientid=self.clientid),
            'linestop': mqttcommon.RequestClient(
                _topics['line'], 'stop', clientid=self.clientid),

            'stop': mqttcommon.RequestClient(
                _topics['node'], 'stop', clientid=self.clientid),

            'stopall': mqttcommon.RequestClient(
                _topics['prefix'], 'stopall', clientid=self.clientid),

            'error': mqttcommon.ErrorClient(_topics['prefix'],
                                            callback=error_cb),
        }

        self.client = mqttcommon.MQTTClient(host, port=port,
                                            topics=self.topics)

    def error_cb(self, message, relative_topic):  # pylint:disable=no-self-use
        """Callback on 'error' topic."""
        msg = message.payload.decode('utf-8')
        print('SERIAL ERROR:%s:%s' % (relative_topic, msg))

    @classmethod
    def from_opts_dict(cls, broker, broker_port, prefix, site, **_):
        """Create class from argparse entries."""
        return cls(broker, port=broker_port, prefix=prefix, site=site)

    # # # # #
    # line  #
    # # # # #
    def line_handler(self, message, archi, num):  # pylint:disable=no-self-use
        """Handle line received from nodes."""
        line = message.payload.decode('utf-8')
        print('line_handler(%s-%s): %s' % (archi, num, line))

    # # # # # # #
    # linestart #
    # # # # # # #
    def do_linestart(self, arg):
        """Start line mode to given node: ARCHI NUM"""
        try:
            archi, num = shlex.split(arg)
            num = int(num)
            if archi not in self.ARCHIS:
                print('archi not in %s' % (self.ARCHIS,))
                raise ValueError()

        except ValueError:
            self.help_linestart('Usage: ')
            return 0

        self._do_linestart(archi, num)

    def _do_linestart(self, archi, num):
        topic = self.topics['linestart']

        ret = topic.request(self.client, b'', timeout=5, archi=archi, num=num)
        if ret:
            print(ret.decode('utf-8'))

    def help_linestart(self, prefix=''):
        """Help linestart command."""
        print(prefix, end='')
        print(self.LINESTART_USAGE, end='')

    # # # # # # #
    # linewrite #
    # # # # # # #
    def do_linewrite(self, arg):
        """Write line to given node: ARCHI NUM MESSAGE."""
        try:
            archi, num, message = shlex.split(arg)
            num = int(num)
        except ValueError:
            self.help_linewrite('Usage: ')
            return 0

        msg = message.decode('utf-8')  # Expect stdin to be utf-8

        payload = msg.encode('utf-8')
        self.topics['line'].send(self.client, archi, num, payload)

    def help_linewrite(self, prefix=''):
        """Help linewrite command."""
        print(prefix, end='')
        print(self.LINEWRITE_USAGE, end='')

    # # # # #
    # stop  #
    # # # # #
    def do_stop(self, arg):
        """Stop node redirection: ARCHI NUM."""
        try:
            archi, num = shlex.split(arg)
            num = int(num)
        except ValueError:
            self.help_stop('Usage: ')
            return 0

        topic = self.topics['stop']
        ret = topic.request(self.client, b'', timeout=5, archi=archi, num=num)
        if ret:
            print(ret.decode('utf-8'))

    def help_stop(self, prefix=''):
        """Help stop command."""
        print(prefix, end='')
        print(self.STOP_USAGE, end='')

    # # # # # #
    # stopall #
    # # # # # #
    def do_stopall(self, _):
        """Stop all nodes redirection."""
        topic = self.topics['stopall']
        ret = topic.request(self.client, b'', timeout=5)
        if ret:
            print(ret.decode('utf-8'))

    def help_stopall(self, prefix=''):
        """Help stopall command."""
        print(prefix, end='')
        print(self.STOPALL_USAGE, end='')

    def run(self):
        """Run client and shell."""
        self.client.start()
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            pass
        self.client.stop()


def main():
    """SerialAgent shell client."""
    opts = PARSER.parse_args()
    shell = SerialShell.from_opts_dict(**vars(opts))
    shell.run()


if __name__ == '__main__':
    main()
