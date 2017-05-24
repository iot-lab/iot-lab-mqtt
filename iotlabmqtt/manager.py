# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

try:
    import ConfigParser as configparser
except ImportError:  # pragma: no cover
    import configparser

import sys
import argparse

from . import common
from . import iotlabapi
from . import mqttcommon
from . import process


EPILOG = (
    'Options can also be set by giving a `CONFIG_FILE` path.\n'
    'Where the config file format is:\n'
    '\n'
    '    [DEFAULT]\n'
    '    --broker-port = 8883\n'
    '    # --any-other-argument = arg_value\n'
    '    broker = BROKER_ADDRESS\n'
    '\n'
    'This allows running it with IoT-LAB "script" execution feature\n'
)
PARSER = common.MQTTAgentArgumentParser(
    epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
iotlabapi.parser_add_iotlabapi_args(PARSER)


MANAGER_PROCESS = {
    'serial': ['iotlab-mqtt-serial', 'ARGS_prefix', 'ARGS_mqtt'],
    'node': ['iotlab-mqtt-node', 'ARGS_prefix', 'ARGS_mqtt', 'ARGS_iotlabapi'],
    'radiosniffer': ['iotlab-mqtt-radiosniffer', 'ARGS_prefix', 'ARGS_mqtt',
                     'ARGS_iotlabapi'],
    'process': ['iotlab-mqtt-process', 'ARGS_prefix', 'ARGS_mqtt'],
}


def arguments_substitution_dict(prefix, **objs):
    """Return dict of arguments list for ``prefix`` and ``**objs args`` list.

    Construct a dict with 'ARG_{name}: [args_list]' entries in the dict.

    For prefix, args will be ['--prefix', prefix].
    For objects in ``**objs``, arguments list is got by calling
    'to_argparse_list' method.
    """
    ret = {}
    ret['ARGS_prefix'] = ['--prefix', prefix]

    for name, obj in objs.items():
        ret['ARGS_%s' % name] = obj.to_argparse_list()

    return ret


def process_arguments_dict(process_dict, args_dict):
    """Return dict of processes with arguments.

    Enrich process_dict arguments with args_dict values.
    """
    ret = {}
    for name, args_list in process_dict.items():
        ret[name] = _substitute_arguments(args_list, args_dict)
    return ret


def _substitute_arguments(args_list, args_dict):
    """Return list of arguments.

    >>> args_dict = {'ARGS_prefix': ['--prefix', 'PREFIX'],
    ...              'ARGS_mqtt': ['--broker-port', '8884', 'localhost']}
    >>> args_list = ['command', 'argument', 'ARGS_prefix', 'ARGS_mqtt']

    >>> expected = ['command', 'argument', '--prefix', 'PREFIX',
    ...             '--broker-port', '8884', 'localhost']

    >>> _substitute_arguments(args_list, args_dict) == expected
    True
    """
    return [arg for name in args_list for arg in args_dict.get(name, [name])]


class MQTTManagerAgent(process.MQTTProcessAgent):
    """Agent Manager Agent implementation for MQTT."""
    AGENTTOPIC = 'iot-lab/manager/{site}'

    def __init__(self, client, prefix='', agenttopic=None,
                 process_args_dict=None):
        # Default value
        process_args_dict = process_args_dict or {}

        super().__init__(client, prefix=prefix, agenttopic=agenttopic)

        self.process_args_dict = process_args_dict

    # Disable unused 'Process' methods

    def cb_new(self, _):
        """Alloc a new process id."""
        return self._disabled_method_for_manager()

    def cb_free(self, message):
        """Free given process id."""
        return self._disabled_method_for_manager()

    def cb_procrun(self, message, procid):
        """Run command for process id."""
        return self._disabled_method_for_manager()

    @staticmethod
    def _disabled_method_for_manager():
        return 'Method not available for manager'.encode('utf-8')

    def start(self):
        """Start Agent."""
        super().start()
        self.start_managed_processes()

    def stop(self):
        """Stop agent."""
        self.process.stop()
        super().stop()

    def start_managed_processes(self):
        """Start all managed processes."""
        for name, args in self.process_args_dict.items():
            self._start_process(name, args)

    def _start_process(self, name, args):
        """Start process ``name`` with ``args``."""
        print('Starting managed process: %s' % name)
        self.process.new(name)
        self.process[name].run(args)

    @classmethod
    def from_opts_dict(cls, prefix, agenttopic=None, **kwargs):
        """Create class from argparse entries."""
        api = iotlabapi.IoTLABAPI.from_opts_dict(**kwargs)
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)

        prefix = cls._prefix_set_expid_and_user_from_api(prefix, api)

        args_dict = arguments_substitution_dict(
            prefix, iotlabapi=api, mqtt=client)
        process_args_dict = process_arguments_dict(MANAGER_PROCESS, args_dict)

        return cls(client, prefix, agenttopic=agenttopic,
                   process_args_dict=process_args_dict)

    @staticmethod
    def _prefix_set_expid_and_user_from_api(prefix, iotlab_api):
        """Configure  ``prefix`` from ``iotlab_api``.

        Replaces ``{prefix}`` and ``{expid}`` entries by their value.
        """
        user = iotlab_api.username
        expid = iotlab_api.expid
        return prefix.format(user=user, expid=expid)


def arguments_from_argv_or_config(argv):
    """Return parse_args argument from ``argv``.

    Try reading arguments frmo config file or return regular arguments.
    """
    try:
        # Read config file
        (configfile,) = argv[1:]
        return _args_from_configfile(configfile)
    except (ValueError, IOError):
        # Default
        return argv[1:]


def _args_from_configfile(cfgfile):
    args_dict = _args_dict_from_configfile(cfgfile, section='DEFAULT')
    return _args_from_args_dict(args_dict)


def _args_dict_from_configfile(cfgfile, section='DEFAULT'):
    """Read arguments dict from ``cfgfile`` section ``section``."""
    cfg = configparser.ConfigParser()

    # Read and error if non existent file
    cfg.readfp(open(cfgfile), cfgfile)  # pylint:disable=deprecated-method

    # Save to dict
    return dict(cfg.items(section))


def _args_from_args_dict(args_dict):
    args = []
    for name, value in args_dict.items():
        if name.startswith('--'):
            args.append(name)
        args.append(value)

    return args


def main():
    """Run manager agent."""
    args = arguments_from_argv_or_config(sys.argv)
    opts = PARSER.parse_args(args)

    aggr = MQTTManagerAgent.from_opts_dict(**vars(opts))
    aggr.run()
