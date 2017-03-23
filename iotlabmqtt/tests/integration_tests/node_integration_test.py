# -*- coding:utf-8 -*-
"""Integration tests for IoT-LAB MQTT radiosniffer client and server."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import contextlib
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import mock

from iotlabmqtt import node
from iotlabmqtt.clients import node as node_client

from . import IntegrationTestCase


class NodeIntegrationTest(IntegrationTestCase):
    """Test node client and server using a broker."""
    @contextlib.contextmanager
    def start_client_and_server(self, brokerport):
        """Start node client and server context manager.

        Yields client and stdout mock.
        """
        # pylint:disable=attribute-defined-outside-init
        args = ['localhost', '--broker-port', '%s' % brokerport,
                '--prefix', 'node/test/prefix']
        args += ['--experiment-id', '12345',
                 '--iotlab-user', 'us3rn4me',
                 '--iotlab-password', 'p4sswd']
        opts = node.PARSER.parse_args(args)
        with mock.patch('iotlabcli.experiment.get_experiment') as get_exp:
            get_exp.return_value = {'state': 'Running'}
            server = node.MQTTNodeAgent.from_opts_dict(**vars(opts))

        assert server.iotlabapi.expid == 12345
        assert server.iotlabapi.api.auth.username == 'us3rn4me'
        assert server.iotlabapi.api.auth.password == 'p4sswd'
        server.iotlabapi.api = None  # Breaks on calls

        server.start()
        self.server = server

        try:
            args = ['localhost', '--broker-port', '%s' % brokerport,
                    '--prefix', 'node/test/prefix',
                    '--site', server.HOSTNAME]
            opts = node_client.PARSER.parse_args(args)
            client = node_client.NodeShell.from_opts_dict(**vars(opts))
            client.start()
            try:
                with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
                    yield client, stdout
            finally:
                client.stop()
        finally:
            server.stop()

    def test_node_agent_normal_cases(self):
        """Test node agent normal case."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_node_agent_normal_cases(client, stdout)

    @mock.patch('iotlabcli.node.node_command')
    def _test_node_agent_normal_cases(self, client, stdout, node_command=None):
        """Normal cases for node agent."""
        node_host = 'm3-1.%s.iot-lab.info' % self.server.HOSTNAME

        # Reset
        node_command.return_value = {'0': [node_host]}
        client.onecmd('reset m3 1')
        self.assertEqual(stdout.getvalue(), '')

        # Reset with error
        node_command.return_value = {'1': [node_host]}
        client.onecmd('reset m3 1')
        out = 'Execution failed on node\n'
        self.assertEqual(stdout.getvalue(), out)
        stdout.seek(0)
        stdout.truncate(0)

        # Power ON
        node_command.return_value = {'0': [node_host]}
        client.onecmd('poweron m3 1')
        self.assertEqual(stdout.getvalue(), '')

        node_command.return_value = {'1': [node_host]}
        client.onecmd('poweron m3 1')
        out = 'Execution failed on node\n'
        self.assertEqual(stdout.getvalue(), out)
        stdout.seek(0)
        stdout.truncate(0)

        # Power OFF
        node_command.return_value = {'0': [node_host]}
        client.onecmd('poweroff m3 1')
        self.assertEqual(stdout.getvalue(), '')

        node_command.return_value = {'1': [node_host]}
        client.onecmd('poweroff m3 1')
        out = 'Execution failed on node\n'
        self.assertEqual(stdout.getvalue(), out)
        stdout.seek(0)
        stdout.truncate(0)

    def test_node_agent_update(self):
        """Test node agent update with firmware."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_node_agent_update(client, stdout)

    @mock.patch('iotlabcli.node.node_command')
    def _test_node_agent_update(self, client, stdout, node_command=None):
        """Update firmware."""

        node_host = 'm3-1.%s.iot-lab.info' % self.server.HOSTNAME
        firmware_path = self.file_path('m3_firmware.elf')
        firmware_sha1 = '2386ee'

        # pylint:disable=unused-argument
        # pylint:disable=protected-access
        def _node_cmd(api, cmd, exp_id, nodes, fw_path):
            """Got issues when file was not flushed, so verify content."""
            with open(fw_path, mode='rb') as fw_:
                data = fw_.read()
                self.assertEqual(data, b'ELF32')

                sha1 = node.common.short_hash(data)
                self.assertTrue(fw_path.endswith('--sha1:%s' % sha1))
            return mock.DEFAULT
        node_command.side_effect = _node_cmd

        # Update
        node_command.return_value = {'0': [node_host]}
        client.onecmd('update m3 1 %s' % firmware_path)
        self.assertEqual(stdout.getvalue(), '')
        self.assertTrue(node_command.called)

        # Verify call args
        api, cmd, exp_id, nodes, fw_path = node_command.call_args[0]
        self.assertEqual(
            (api, cmd, exp_id, nodes),
            (self.server.iotlabapi.api, 'update', 12345, [node_host]))
        # Verify content with sha1
        self.assertTrue(fw_path.endswith('--sha1:%s' % firmware_sha1))

        # Test error
        node_command.return_value = {'1': [node_host]}
        client.onecmd('update m3 1 %s' % firmware_path)
        out = 'Execution failed on node\n'
        self.assertEqual(stdout.getvalue(), out)
        stdout.seek(0)
        stdout.truncate(0)

    def test_node_agent_update_idle(self):
        """Test node agent update with firmware idle."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_node_agent_update_idle(client, stdout)

    @mock.patch('iotlabcli.node.node_command')
    def _test_node_agent_update_idle(self, client, stdout, node_command=None):
        """Update firmware with idle."""

        node_host = 'm3-1.%s.iot-lab.info' % self.server.HOSTNAME
        idle_sha1 = 'b4b38e'

        # Update
        node_command.return_value = {'0': [node_host]}
        client.onecmd('update m3 1')
        self.assertEqual(stdout.getvalue(), '')
        self.assertTrue(node_command.called)

        # Verify firmware call
        firmware_path = node_command.call_args[0][-1]
        self.assertTrue(firmware_path.endswith('--sha1:%s' % idle_sha1))
