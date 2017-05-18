# -*- coding: utf-8 -*-

"""IoT-LAB MQTT Node agent client"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os

import iotlabmqtt.node
from iotlabmqtt import common
from iotlabmqtt import mqttcommon
from . import common as clientcommon

PARSER = common.MQTTAgentArgumentParser()
clientcommon.parser_add_site_arg(PARSER)


class NodeShell(clientcommon.CmdShell):
    """Node Agent Shell.

    :param client: mqttclient instance
    :param prefix: topics prefix
    :param site: agent site
    """

    RESET_USAGE = ('reset ARCHI NUM\n'
                   '  ARCHI: m3/a8\n'
                   '  NUM:   node num\n')

    UPDATE_USAGE = ('update ARCHI NUM FIRMWAREPATH\n'
                    '  ARCHI: m3/a8\n'
                    '  NUM:   node num\n'
                    '  FIRMWAREPATH: Path to the firmware.\n'
                    '                Idle firmware if not provided\n')

    POWERON_USAGE = ('poweron ARCHI NUM\n'
                     '  ARCHI: m3/a8\n'
                     '  NUM:   node num\n')
    POWEROFF_USAGE = ('poweroff ARCHI NUM\n'
                      '  ARCHI: m3/a8\n'
                      '  NUM:   node num\n')

    SERVER = iotlabmqtt.node.MQTTNodeAgent

    def __init__(self, client, prefix, site=None):
        assert site is not None
        super().__init__()

        self.clientid = clientcommon.clientid('serialclient')

        staticfmt = {'site': site}
        _topics = mqttcommon.generate_topics_dict(
            self.SERVER.TOPICS, prefix, self.SERVER.AGENTTOPIC, staticfmt)

        _print_wrapper = self.async_print_handle_readlinebuff()
        error_cb = _print_wrapper(self.error_cb)

        self.topics = {
            'reset': mqttcommon.RequestClient(
                _topics['node'], 'reset', clientid=self.clientid),
            'update': mqttcommon.RequestClient(
                _topics['node'], 'update', clientid=self.clientid),
            'poweron': mqttcommon.RequestClient(
                _topics['node'], 'poweron', clientid=self.clientid),
            'poweroff': mqttcommon.RequestClient(
                _topics['node'], 'poweroff', clientid=self.clientid),

            'error': mqttcommon.ErrorClient(_topics['agenttopic'],
                                            callback=error_cb),
        }

        self.client = client
        self.client.topics = list(self.topics.values())

    def error_cb(self, message, relative_topic):  # pylint:disable=no-self-use
        """Callback on 'error' topic."""
        msg = message.payload.decode('utf-8')
        print('NODE ERROR: %s: %s' % (relative_topic, msg))

    @classmethod
    def from_opts_dict(cls, prefix, site, **kwargs):
        """Create class from argparse entries."""
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix=prefix, site=site)

    # # # # #
    # reset #
    # # # # #
    def do_reset(self, arg):
        """Reset node cpu: ARCHI NUM."""
        archi, num = self.cmd_split(arg)
        num = int(num)

        topic = self.topics['reset']
        ret = topic.request(self.client, b'', timeout=15,
                            archi=archi, num=num)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_reset(self):
        """Help reset command."""
        print(self.RESET_USAGE, end='')

    # # # # # #
    # Update  #
    # # # # # #
    def do_update(self, arg):
        """Update node firmware: ARCHI NUM FIRMWAREPATH."""
        splitted = self.cmd_split(arg)
        try:
            archi, num, firmware_path = splitted
        except ValueError:
            archi, num = splitted
            firmware = None  # Idle
        else:
            firmware = self._read_file(firmware_path, 'b')
        num = int(num)

        topic = self.topics['update']
        ret = topic.request(self.client, firmware, timeout=60,
                            archi=archi, num=num)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    @staticmethod
    def _read_file(file_path, opt=''):
        """Open and read a file.

        Expands user directory
        """
        try:
            file_path = os.path.expanduser(file_path)  # expand '~'
            with open(file_path, 'r' + opt) as _fd:
                return _fd.read()
        except (IOError, OSError) as err:
            print('Could not open file: %s' % err)
            raise ValueError()

    def help_update(self):
        """Help update command."""
        print(self.UPDATE_USAGE, end='')

    # # # # # #
    # poweron #
    # # # # # #
    def do_poweron(self, arg):
        """Power ON node: ARCHI NUM."""
        archi, num = self.cmd_split(arg)
        num = int(num)

        topic = self.topics['poweron']
        ret = topic.request(self.client, b'', timeout=15,
                            archi=archi, num=num)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_poweron(self):
        """Help poweron command."""
        print(self.POWERON_USAGE, end='')

    # # # # # # #
    # poweroff  #
    # # # # # # #
    def do_poweroff(self, arg):
        """Power OFF node: ARCHI NUM."""
        archi, num = self.cmd_split(arg)
        num = int(num)

        topic = self.topics['poweroff']
        ret = topic.request(self.client, b'', timeout=15,
                            archi=archi, num=num)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_poweroff(self):
        """Help poweroff command."""
        print(self.POWEROFF_USAGE, end='')

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
    shell = NodeShell.from_opts_dict(**vars(opts))
    shell.run()
