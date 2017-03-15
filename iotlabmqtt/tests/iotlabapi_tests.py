# -*- coding:utf-8 -*-

"""iotlabapi module tests."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import argparse

import mock

from iotlabcli.rest import HTTPError
from iotlabmqtt import iotlabapi

from . import TestCaseImproved

# pylint:disable=invalid-name
# patch StringIO: Instance of 'dict' has no 'getvalue' member
# pylint:disable=no-member


class IoTLABAPITestInit(TestCaseImproved):
    """Test IoTLABAPI __init__."""

    def setUp(self):
        self.parser = argparse.ArgumentParser()
        iotlabapi.parser_add_iotlabapi_args(self.parser)

        self.get_experiment = mock.patch(
            'iotlabcli.experiment.get_experiment').start()
        self.get_experiment.return_value = {'state': 'Running'}
        self.stdout = mock.patch('sys.stdout', new_callable=StringIO).start()

    def tearDown(self):
        mock.patch.stopall()

    def test_init_simple(self):
        """Test IoTLABAPI init cases."""
        # Test simple, all args and running experiment

        args = ['--experiment-id', '12345',
                '--iotlab-user', 'us3rn4me',
                '--iotlab-password', 'p4sswd']
        opts = self.parser.parse_args(args)

        api = iotlabapi.IoTLABAPI.from_opts_dict(**vars(opts))

        self.get_experiment.assert_called_with(api.api, 12345, 'state')

        self.assertEqual(api.expid, 12345)
        self.assertEqual(api.api.auth.username, 'us3rn4me')
        self.assertEqual(api.api.auth.password, 'p4sswd')

        out = ''
        self.assertEqual(self.stdout.getvalue(), out)

    @mock.patch('iotlabcli.auth.get_user_credentials')
    def test_init_user_password_authcli(self, get_cred):
        """Test IoTLABAPI user/password from rcfile."""
        get_cred.return_value = ('user', 'password')

        # User and password from rcfile
        args = ['--experiment-id', '12345']
        opts = self.parser.parse_args(args)

        api = iotlabapi.IoTLABAPI.from_opts_dict(**vars(opts))

        self.get_experiment.assert_called_with(api.api, 12345, 'state')
        get_cred.assert_called_with(None, None)
        self.assertEqual(api.expid, 12345)
        self.assertEqual(api.api.auth.username, 'user')
        self.assertEqual(api.api.auth.password, 'password')

        out = ''
        self.assertEqual(self.stdout.getvalue(), out)

    @mock.patch('iotlabcli.auth.get_user_credentials')
    def test_init_no_user_password(self, get_cred):
        """Test IoTLABAPI no user/password Auth fails."""
        get_cred.return_value = (None, None)

        err = HTTPError(None, 401, 'msg', None, None)
        self.get_experiment.side_effect = err

        args = ['--experiment-id', '12345']
        opts = self.parser.parse_args(args)

        self.assertRaises(SystemExit,
                          iotlabapi.IoTLABAPI.from_opts_dict, **vars(opts))

        self.assertTrue(self.get_experiment.called)
        get_cred.assert_called_with(None, None)

        out = (
            'IoT-LAB API not authorized.\n'
            'Provide ``--iotlab-user`` and ``--iotlab-password`` options.\n'
            'Or register them using ``auth-cli --user USERNAME``\n')
        self.assertEqual(self.stdout.getvalue(), out)

    @mock.patch('iotlabcli.helpers.get_current_experiment')
    def test_init_no_experiment(self, get_cur_exp):
        """Test IoTLABAPI no experiment provided."""
        err = ValueError("You have no 'Running' experiment")
        get_cur_exp.side_effect = err

        args = ['--iotlab-user', 'us3rn4me',
                '--iotlab-password', 'p4sswd']
        opts = self.parser.parse_args(args)

        self.assertRaises(SystemExit,
                          iotlabapi.IoTLABAPI.from_opts_dict, **vars(opts))

        self.assertTrue(get_cur_exp.called)
        self.assertFalse(self.get_experiment.called)

        out = "You have no 'Running' experiment\n"
        self.assertEqual(self.stdout.getvalue(), out)

    def test_init_exp_not_running(self):
        """Test IoTLABAPI no experiment provided."""
        self.get_experiment.return_value = {'state': 'Error'}

        args = ['--experiment-id', '12345',
                '--iotlab-user', 'us3rn4me',
                '--iotlab-password', 'p4sswd']
        opts = self.parser.parse_args(args)

        self.assertRaises(SystemExit,
                          iotlabapi.IoTLABAPI.from_opts_dict, **vars(opts))
        self.assertTrue(self.get_experiment.called)

        out = "Experiment 12345 not running 'Error'\n"
        self.assertEqual(self.stdout.getvalue(), out)


class IoTLABAPITest(TestCaseImproved):
    """Test IoTLABAPI."""

    def setUp(self):
        get_experiment = mock.patch(
            'iotlabcli.experiment.get_experiment').start()
        get_experiment.return_value = {'state': 'Running'}

        parser = argparse.ArgumentParser()
        iotlabapi.parser_add_iotlabapi_args(parser)
        args = ['--iotlab-user', 'user',
                '--iotlab-password', 'password',
                '--experiment-id', '12345']
        opts = parser.parse_args(args)
        self.api = iotlabapi.IoTLABAPI.from_opts_dict(**vars(opts))

        # Prevent un-patched calls
        self.api.api = mock.MagicMock(spec_set=True)

    def tearDown(self):
        mock.patch.stopall()

    def test_set_sniffer_channel_localhost(self):
        """Test IoTLABAPI set_sniffer_channel for localhost."""

        # Simple 'localhost' test
        ret = self.api.set_sniffer_channel(11, 'localhost', 30001)
        self.assertEqual(ret, {'30001': ''})

        # Multiple 'localhost' test
        ret = self.api.set_sniffer_channel(11, 'localhost',
                                           30001, 30002, 30003)
        self.assertEqual(ret, {'30001': '', '30002': '', '30003': ''})

    @staticmethod
    def _add_profile_mock(name, profile):  # pylint:disable=unused-argument
        """Add_profile mock."""
        return {'create': name}

    def test_set_sniffer_channel_m3_a8(self):
        """Test IoTLABAPI set_sniffer_channel for m3 and a8."""
        self.api.api.mock_add_spec(['add_profile', 'node_command'])
        self.api.api.add_profile.side_effect = self._add_profile_mock

        self.api.api.node_command.return_value = {
            '0': ['m3-42.%s.iot-lab.info' % self.api.HOSTNAME],
        }
        ret = self.api.set_sniffer_channel(11, 'm3', 42)
        self.assertEqual(ret, {'42': ''})

        self.api.api.node_command.return_value = {
            '0': ['m3-42.%s.iot-lab.info' % self.api.HOSTNAME,
                  'm3-66.%s.iot-lab.info' % self.api.HOSTNAME],
        }
        ret = self.api.set_sniffer_channel(11, 'm3', 42, 66)
        self.assertEqual(ret, {'42': '', '66': ''})

        # Command fails, message replaced
        self.api.api.node_command.return_value = {
            '1': ['m3-42.%s.iot-lab.info' % self.api.HOSTNAME],
        }
        ret = self.api.set_sniffer_channel(11, 'm3', 42)
        self.assertEqual(ret, {'42': 'Execution failed on node'})

        self.api.api.node_command.return_value = {
            '0': ['a8-128.%s.iot-lab.info' % self.api.HOSTNAME],
        }
        ret = self.api.set_sniffer_channel(11, 'a8', 128)
        self.assertEqual(ret, {'128': ''})

    def test_set_sniffer_channel_invalid_archi(self):
        """Test IoTLABAPI set_sniffer_channel for not supported archi."""

        ret = self.api.set_sniffer_channel(11, 'des', 1)
        err = 'Create profile failed: Archi: des not currently supported'
        self.assertEqual(ret, {'1': err})

    def test_set_sniffer_channel_fail_create_profile(self):
        """Test IoTLABAPI set_sniffer_channel add_profile fail."""
        # pylint:disable=redefined-variable-type
        self.api.api.mock_add_spec(['add_profile'])

        self.api.api.add_profile.return_value = "ERROR HTTP"
        ret = self.api.set_sniffer_channel(11, 'm3', 42)
        err = ('Create profile failed: '
               'Add profile failed: \'"ERROR HTTP"\'')
        self.assertEqual(ret, {'42': err})

        self.api.api.add_profile.return_value = {'0': 'iotlabmqtt_11_m3'}
        ret = self.api.set_sniffer_channel(11, 'm3', 42)
        err = ('Create profile failed: '
               'Add profile failed: \'{"0": "iotlabmqtt_11_m3"}\'')
        self.assertEqual(ret, {'42': err})

    def test_set_sniffer_channel_fail_set_profile(self):
        """Test IoTLABAPI set_sniffer_channel fail node_command."""
        self.api.api.mock_add_spec(['add_profile', 'node_command'])
        self.api.api.add_profile.side_effect = self._add_profile_mock

        self.api.api.node_command.side_effect = RuntimeError('FAILED')
        ret = self.api.set_sniffer_channel(11, 'm3', 42)
        err = "IoT-LAB Request 'profile' error: 'FAILED'"
        self.assertEqual(ret, {'42': err})

    def test_node_commands(self):
        """Test IoTLABAPI commands using node_command."""
        self.api.api.mock_add_spec(['node_command'])
        node = 'm3-42.%s.iot-lab.info' % self.api.HOSTNAME
        self.api.api.node_command.return_value = {
            '0': [node]
        }

        ret = self.api.reset('m3', 42)
        self.assertEqual(ret, {'42': ''})
        self.api.api.node_command.assert_called_with('reset', 12345, [node])

        ret = self.api.poweron('m3', 42)
        self.assertEqual(ret, {'42': ''})
        self.api.api.node_command.assert_called_with('start', 12345, [node])

        ret = self.api.poweroff('m3', 42)
        self.assertEqual(ret, {'42': ''})
        self.api.api.node_command.assert_called_with('stop', 12345, [node])

    @mock.patch('iotlabcli.node.node_command')
    def test_update(self, node_command):
        """Test IoTLABAPI update."""
        node = 'm3-42.%s.iot-lab.info' % self.api.HOSTNAME
        node_command.return_value = {'0': [node]}

        ret = self.api.update('tutorial_m3.elf', 'm3', 42)
        self.assertEqual(ret, {'42': ''})
        node_command.assert_called_with(self.api.api, 'update', 12345,
                                        [node], 'tutorial_m3.elf')

    def test_update_no_firmware_file(self):
        """Test IoTLABAPI update without firmware file."""
        ret = self.api.update('/tmp/non/existant/file', 'm3', 42)

        # Use startswith because of python2/python3 string printing compat
        error = ret['42']
        error_start = ("IoT-LAB Request 'update' error: "
                       "'[Errno 2] No such file or directory: ")
        self.assertTrue(error.startswith(error_start))
