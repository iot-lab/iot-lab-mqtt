# -*- coding: utf-8 -*-

"""IoT-LAB MQTT Monitoring client"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622


from iotlabmqtt import common
from iotlabmqtt import mqttcommon
# from iotlabmqtt import serial

from . import common as clientcommon

PARSER = common.MQTTAgentArgumentParser()


class MonitoringShell(clientcommon.CmdShell):
    """Monitoring Agent Shell.

    :param client: mqttclient instance
    :param prefix: topics prefix
    """
    PROBE_USAGE = 'probe\n'

    def __init__(self, client, prefix):
        super().__init__()
        self.clientid = clientcommon.clientid('serialclient')

        _print_wrapper = self.async_print_handle_readlinebuff()
        announce_cb = _print_wrapper(self.announce_handler)
        self.topics = {
            'discover': mqttcommon.DiscoverClient(prefix, announce_cb),
        }

        self.client = client
        self.client.topics = list(self.topics.values())

    @classmethod
    def from_opts_dict(cls, prefix, **kwargs):
        """Create class from argparse entries."""
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix=prefix)

    def announce_handler(self, message, agenttopic):
        print('ANNOUNCED AGENT: %s' % agenttopic)

        # TODO subscribe

    def do_probe(self, arg):
        """Probe existing agents."""
        self.topics['discover'].probe(self.client)

    def help_probe(self):
        """Help discover command."""
        print(self.PROBE_USAGE, end='')

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
    """Monitoring shell client.

    :param opts: If provided, don't parse command line but use it instead
    :type opts: argparse Namespace object
    """
    opts = opts or PARSER.parse_args()
    shell = MonitoringShell.from_opts_dict(**vars(opts))
    shell.run()
