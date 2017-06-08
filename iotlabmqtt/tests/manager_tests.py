# -*- coding:utf-8 -*-

"""Manager agent tests."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622


import os
import tempfile
import textwrap

from iotlabmqtt import manager
from . import TestCaseImproved

# pylint:disable=invalid-name


class ManagerArguentsTestFromConfig(TestCaseImproved):
    """Test Arguments reading from configfile."""

    def setUp(self):
        self.configfile = tempfile.NamedTemporaryFile(mode='w+', delete=True)

    def tearDown(self):
        self.configfile.close()

    def test_arguments_from_config_minimal(self):
        """Test starting from args and configfile with minimal options."""
        os.environ.pop('EXP_ID', '')
        argv = ['localhost']

        config = textwrap.dedent('''\
        [DEFAULT]
        broker = localhost
        ''')
        self.configfile.write(config)
        self.configfile.flush()

        argv = ['manager'] + argv
        args = manager.arguments_from_argv_or_config(argv)
        opts = manager.PARSER.parse_args(args)
        self.assertIsNone(opts.experiment_id)

        config_argv = ['manager', self.configfile.name]
        config_args = manager.arguments_from_argv_or_config(config_argv)
        config_opts = manager.PARSER.parse_args(config_args)
        self.assertEqual(opts, config_opts)

    def test_arguments_from_config_default(self):
        """Test starting from args and configfile with basic options."""
        argv = ['localhost', '--broker-port', '8883',
                '--prefix', 'iotlabmqtt/test/prefix']
        argv += ['--experiment-id', '12345',
                 '--iotlab-user', 'us3rn4me',
                 '--iotlab-password', 'p4sswd']

        config = textwrap.dedent('''\
        [DEFAULT]
        --prefix = iotlabmqtt/test/prefix
        --broker-port = 8883
        --iotlab-user = us3rn4me
        --iotlab-password = p4sswd
        # Automatically deduced values when used with 'run_script'
        --experiment-id = 12345
        broker = localhost
        ''')
        self.configfile.write(config)
        self.configfile.flush()

        argv = ['manager'] + argv
        args = manager.arguments_from_argv_or_config(argv)
        opts = manager.PARSER.parse_args(args)

        config_argv = ['manager', self.configfile.name]
        config_args = manager.arguments_from_argv_or_config(config_argv)
        config_opts = manager.PARSER.parse_args(config_args)
        self.assertEqual(opts, config_opts)
