# -*- coding: utf-8 -*-

"""IoT-LAB MQTT Process agent client"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import json

import iotlabmqtt.process
from iotlabmqtt import common
from iotlabmqtt import mqttcommon

from . import common as clientcommon


PARSER = common.MQTTAgentArgumentParser()
clientcommon.parser_add_site_or_agenttopic_arg(PARSER)


class ProcessShell(clientcommon.CmdShell):
    # pylint:disable=too-many-public-methods
    """Process Agent Shell.

    :param client: mqttclient instance
    :param prefix: topics prefix
    :param site: agent site
    """
    NEW_USAGE = ('new [NAME]\n'
                 '  NAME: optional process identifier\n')
    FREE_USAGE = ('free NAME\n'
                  '  NAME: process identifier\n')
    LIST_USAGE = ('list\n')

    RUN_USAGE = ('run NAME CMD0 [CMD1 [...]]\n'
                 '  NAME: process identifier\n'
                 '  CMD: command arguments\n')
    POLL_USAGE = ('poll NAME\n'
                  '  NAME: process identifier\n')
    KILL_USAGE = ('kill NAME\n'
                  '  NAME: process identifier\n')
    RERUN_USAGE = ('rerun NAME\n'
                   '  NAME: process identifier\n')

    STDINLINE_USAGE = (
        'stdinline NAME message with spaces\n'
        '  NAME: process identifier\n'
        '  Message is sent as utf-8 data with a \\n character\n'
    )
    STDINRAW_USAGE = (
        'stdinraw NAME message with spaces\n'
        '  NAME: process identifier\n'
        '  Message is sent as utf-8 data\n'
    )

    SERVER = iotlabmqtt.process.MQTTProcessAgent

    def __init__(self, client, prefix, site=None, agenttopic=None):
        assert site is not None or agenttopic is not None
        super().__init__()

        self.clientid = clientcommon.clientid('serialclient')

        _topics = self._topics_dict(prefix, site, agenttopic)

        _print_wrapper = self.async_print_handle_readlinebuff()
        stdout_cb = _print_wrapper(self.stdout_cb)
        stderr_cb = _print_wrapper(self.stderr_cb)
        returncode_cb = _print_wrapper(self.returncode_cb)
        error_cb = _print_wrapper(self.error_cb)

        self.topics = {
            'new': mqttcommon.RequestClient(
                _topics['agenttopic'], 'new', clientid=self.clientid),
            'list': mqttcommon.RequestClient(
                _topics['agenttopic'], 'list', clientid=self.clientid),
            'free': mqttcommon.RequestClient(
                _topics['agenttopic'], 'free', clientid=self.clientid),
            'freeall': mqttcommon.RequestClient(
                _topics['agenttopic'], 'freeall', clientid=self.clientid),

            'procrun': mqttcommon.RequestClient(
                _topics['process'], 'run', clientid=self.clientid),
            'procpoll': mqttcommon.RequestClient(
                _topics['process'], 'poll', clientid=self.clientid),
            'prockill': mqttcommon.RequestClient(
                _topics['process'], 'kill', clientid=self.clientid),
            'procrerun': mqttcommon.RequestClient(
                _topics['process'], 'rerun', clientid=self.clientid),

            'procstdin': mqttcommon.InputClient(_topics['procstdin']),
            'procstdout': mqttcommon.OutputClient(_topics['procstdout'],
                                                  callback=stdout_cb),
            'procstderr': mqttcommon.OutputClient(_topics['procstderr'],
                                                  callback=stderr_cb),

            'procret': mqttcommon.OutputClient(_topics['procret'],
                                               callback=returncode_cb),

            'error': mqttcommon.ErrorClient(_topics['agenttopic'],
                                            callback=error_cb),
        }

        self.client = client
        self.client.topics = list(self.topics.values())

    def _topics_dict(self, prefix, site=None, agenttopic=None):
        """Return topics formated for site or agenttopic.

        Allows overwriting default prefix with agenttopic.
        """

        # Prefix topics with 'agenttopic'
        agenttopic = (agenttopic if agenttopic is not None else
                      self.SERVER.AGENTTOPIC)
        staticfmt = {'site': site} if site is not None else {}

        err = 'site required for agenttopic format'
        assert not ('site' in agenttopic and site is None), err

        return mqttcommon.generate_topics_dict(
            self.SERVER.TOPICS, prefix, agenttopic, staticfmt)

    def error_cb(self, message, relative_topic):  # pylint:disable=no-self-use
        """Callback on 'error' topic."""
        msg = message.payload.decode('utf-8')
        print('PROCESS ERROR: %s: %s' % (relative_topic, msg))

    @classmethod
    def from_opts_dict(cls, prefix, site=None, agenttopic=None, **kwargs):
        """Create class from argparse entries."""
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix=prefix, site=site, agenttopic=agenttopic)

    def stdout_cb(self, message, procid):  # pylint:disable=no-self-use
        """Handle messages received from stdout."""
        self._fd_cb('stdout', procid, message)

    def stderr_cb(self, message, procid):  # pylint:disable=no-self-use
        """Handle messages received from stderr."""
        self._fd_cb('stderr', procid, message)

    def _fd_cb(self, fdname, procid, message):
        """Print `message` payload for `fdname` and `procid`."""
        data = message.payload.decode('utf-8', 'replace')
        data = self._repr_without_u_for_unicode_strings(data)
        print('%s(%s): %s' % (fdname, procid, data))

    @staticmethod
    def _repr_without_u_for_unicode_strings(unicode_message):
        """Returns string 'repr' without the leading 'u' for unicode.

        If python2, repr of an unicode string starts with a 'u', remove it
        """
        message = repr(unicode_message)
        if message.startswith('u'):
            message = message[1:]
        return message

    def returncode_cb(self, message, procid):  # pylint:disable=no-self-use
        """Handle returncode sent by process."""
        returncode = message.payload.decode('utf-8', 'replace')
        print('closed(%s): %s' % (procid, returncode))

    def do_new(self, arg):
        """Allocate a new process: [NAME]."""
        args = self.cmd_split(arg)
        if args:
            (name,) = args
        else:
            name = ''

        payload = name.encode('utf-8')  # can be empty

        topic = self.topics['new']
        ret = topic.request(self.client, payload, timeout=5)

        print(ret.decode('utf-8'))

    def help_new(self):
        """Help new command."""
        print(self.NEW_USAGE, end='')

    def do_free(self, arg):
        """Free given process: NAME."""
        (name,) = self.cmd_split(arg)

        payload = name.encode('utf-8')  # can be empty

        topic = self.topics['free']
        ret = topic.request(self.client, payload, timeout=5)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_free(self):
        """Help free command."""
        print(self.FREE_USAGE, end='')

    def do_list(self, _):
        """List processes names."""
        topic = self.topics['list']
        ret = topic.request(self.client, b'', timeout=5)

        # May have errors here but I don't know how to generate it
        # Ignore, its just a simple client
        names = json.loads(ret.decode('utf-8'))
        print([str(n) for n in names])

    def help_list(self):
        """Help list command."""
        print(self.LIST_USAGE, end='')

    def do_run(self, arg):
        """Run command for process name: NAME COMMAND."""
        args = self.cmd_split(arg)
        try:
            name = args[0]
            command = [args[1]] + args[2:]
        except IndexError:
            raise ValueError

        payload = json.dumps(command).encode('utf-8')

        topic = self.topics['procrun']
        ret = topic.request(self.client, payload, timeout=10, procid=name)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_run(self):
        """Help run command."""
        print(self.RUN_USAGE, end='')

    def do_poll(self, arg):
        """Poll process name: NAME."""
        (name,) = self.cmd_split(arg)

        topic = self.topics['procpoll']
        ret = topic.request(self.client, b'', timeout=10, procid=name)
        if ret:
            print(ret.decode('utf-8'))

    def help_poll(self):
        """Help poll command."""
        print(self.POLL_USAGE, end='')

    def do_kill(self, arg):
        """Kill process name: NAME."""
        (name,) = self.cmd_split(arg)

        topic = self.topics['prockill']
        ret = topic.request(self.client, b'', timeout=10, procid=name)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_kill(self):
        """Help kill command."""
        print(self.KILL_USAGE, end='')

    def do_rerun(self, arg):
        """Rerun process name: NAME."""
        (name,) = self.cmd_split(arg)

        topic = self.topics['procrerun']
        ret = topic.request(self.client, b'', timeout=10, procid=name)
        if ret:
            raise RuntimeError(ret.decode('utf-8'))

    def help_rerun(self):
        """Help rerun command."""
        print(self.RERUN_USAGE, end='')

    def do_stdinline(self, arg):
        """Send message to process `name` stdin: NAME MESSAGE.

        Add a newline character
        """
        name, message = self.cmd_split(arg, 1)

        payload = (message + '\n').encode('utf-8')

        self.topics['procstdin'].send(self.client, payload, procid=name)

    def help_stdinline(self):
        """Help stdinline command."""
        print(self.STDINLINE_USAGE, end='')

    def do_stdinraw(self, arg):
        """Send message to process `name` stdin: NAME MESSAGE."""
        name, message = self.cmd_split(arg, 1)

        payload = (message).encode('utf-8')

        self.topics['procstdin'].send(self.client, payload, procid=name)

    def help_stdinraw(self):
        """Help stdinraw command."""
        print(self.STDINRAW_USAGE, end='')

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
    """ProcessAgent shell client.

    :param opts: If provided, don't parse command line but use it instead
    :type opts: argparse Namespace object
    """
    opts = opts or PARSER.parse_args()
    clientcommon.parser_verify_site_and_agenttopic(PARSER, opts)
    shell = ProcessShell.from_opts_dict(**vars(opts))
    shell.run()
