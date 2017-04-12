# -*- coding: utf-8 -*-

"""IoT-LAB MQTT Log agent client"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os
import base64

from iotlabmqtt import common
from iotlabmqtt import mqttcommon

from . import common as clientcommon

PARSER = common.MQTTAgentArgumentParser()


class LogShell(clientcommon.CmdShell):
    """Log messages Shell.

    :param client: mqttclient instance
    :param prefix: topics prefix
    """
    DEVNULL = open(os.devnull, 'w')

    OPEN_USAGE = ('open LOGFILE\n'
                  '  LOGFILE:   csv log file\n')
    CLOSE_USAGE = ('close\n'
                   '  Close current logfile\n')

    def __init__(self, client, prefix):
        super().__init__()

        _print_wrapper = self.async_print_handle_readlinebuff()
        log_cb = _print_wrapper(self.log_handler)

        self.topics = {
            'log': mqttcommon.LogTopic(prefix, log_cb),
        }

        self._logfile = self.DEVNULL

        self.client = client
        self.client.topics = list(self.topics.values())

    @property
    def logfile(self):
        """Current logfile."""
        return self._logfile

    @logfile.setter
    def logfile(self, log_file):
        """Set logfile and close previous one."""
        _logfile = self._logfile

        self._logfile = log_file

        if _logfile != self.DEVNULL:
            _logfile.close()

    @classmethod
    def from_opts_dict(cls, prefix, **kwargs):
        """Create class from argparse entries."""
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix=prefix)

    def do_open(self, arg):
        """Open a logfile."""
        try:
            logfile = open(arg, 'w', buffering=1)
        except (IOError, OSError) as err:
            print('Could not open file: %s' % err)
            raise ValueError()
        else:
            self.logfile = logfile

    def help_open(self):
        """Help open command."""
        print(self.OPEN_USAGE, end='')

    def do_close(self, _=None):
        """Close current logfile."""
        self.logfile = self.DEVNULL

    def help_close(self):
        """Help close command."""
        print(self.CLOSE_USAGE, end='')

    def log_handler(self, message):
        """Callback for logging."""
        self._log_print_message(message)
        self._log_save_message(message)

    @classmethod
    def _log_print_message(cls, message):
        """Print debug message in a readable format."""
        message_fmt = "%.3f %s '%s'"
        message_payload_str = cls._log_payload_str(message.payload)
        message_str = message_fmt % (message.timestamp, message.topic,
                                     message_payload_str)
        print(message_str)

    def _log_save_message(self, message):
        """Save message to logfile."""
        message_fmt = '%.3f;%s;%s\n'
        message_payload_str = base64.b64encode(message.payload)
        message_payload_str = message_payload_str.decode('utf-8')
        message_str = message_fmt % (message.timestamp, message.topic,
                                     message_payload_str)
        self.logfile.write(message_str)
        self.logfile.flush()

    @staticmethod
    def _log_payload_str(payload):
        """Payload representation."""
        try:
            payload_str = payload.decode('utf-8')
        except UnicodeDecodeError:
            payload_fmt = 'BIN: (len %u): hash: %s'
            short_sha1 = common.short_hash(payload)
            payload_str = payload_fmt % (len(payload), short_sha1)
        return payload_str

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
    """Logging shell client.

    :param opts: If provided, don't parse command line but use it instead
    :type opts: argparse Namespace object
    """
    opts = opts or PARSER.parse_args()
    shell = LogShell.from_opts_dict(**vars(opts))
    shell.run()
