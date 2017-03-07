# -*- coding:utf-8 -*-

"""iotlabapi module tests."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import argparse

import mock

from iotlabmqtt import iotlabapi

from . import TestCaseImproved

# pylint:disable=invalid-name


class IoTLABAPITest(TestCaseImproved):
    """Test IoTLABAPI."""
    def setUp(self):
        parser = argparse.ArgumentParser()
        iotlabapi.parser_add_iotlabapi_args(parser)
        args = ['--iotlab-user', 'user',
                '--iotlab-password', 'password',
                '--experiment-id', '12345']
        opts = parser.parse_args(args)
        self.api = iotlabapi.IoTLABAPI.from_opts_dict(**vars(opts))

        # Prevent un-patched calls
        self.api.api = mock.MagicMock(spec_set=True)

    def test_set_sniffer_channel_localhost(self):
        """Test IoTLABAPI set_sniffer_channel for localhost."""

        # Simple 'localhost' test
        ret = self.api.set_sniffer_channel(11, 'localhost', 30001)
        self.assertEqual(ret, {'30001': ''})

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
        err = "Update profile failed: IoT-LAB Request error: 'FAILED'"
        self.assertEqual(ret, {'42': err})
