# -*- coding:utf-8 -*-
"""Integration tests for IoT-LAB MQTT radiosniffer client and server."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os
import contextlib
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import mock

from iotlabmqtt import node
from iotlabmqtt.clients import node as node_client

from . import IntegrationTestCase
from .. import TestCaseImproved

# pylint:disable=invalid-name


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

    def test_node_agent_update_idle_not_supported(self):
        """Test node agent update for an archi not supported."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_node_agent_update_idle_not_supported(client, stdout)

    @mock.patch('iotlabcli.node.node_command')
    def _test_node_agent_update_idle_not_supported(self, client, stdout,
                                                   node_command=None):
        """Update firmware with idle not supported."""

        # Use a 'custom' archi where idle is not implemented

        # Update
        node_command.side_effect = RuntimeError()
        client.onecmd('update samr21 1')
        self.assertFalse(node_command.called)

        out = 'Idle firmware not handled for samr21\n'
        self.assertEqual(stdout.getvalue(), out)
        stdout.seek(0)
        stdout.truncate(0)

    def test_node_agent_error_cb(self):
        """Test node client error_cb."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_node_agent_error_cb(client, stdout)

    def _test_node_agent_error_cb(self, client, stdout):
        """Call node client error cb."""
        topic = self.server.topics['error'].topic
        topic = topic.replace('/error/', '')
        topic = os.path.join(topic, 'a/topic/on/server')

        error = 'test manual error'.encode('utf-8')
        self.server.topics['error'].publish_error(self.server.client, topic,
                                                  error)

        err = ('NODE ERROR: a/topic/on/server: test manual error\n'
               '(Cmd) ')

        self.assertEqualTimeout(stdout.getvalue, err, 2)
        stdout.seek(0)
        stdout.truncate(0)


@mock.patch('sys.stdout', new_callable=StringIO)
class NodeClientErrorTests(TestCaseImproved):
    """Test Node parsing errors."""
    def setUp(self):
        args = ['localhost', '--broker-port', '%s' % 54321,
                '--prefix', 'node/test/prefix',
                '--site', node.MQTTNodeAgent.HOSTNAME]
        opts = node_client.PARSER.parse_args(args)
        self.client = node_client.NodeShell.from_opts_dict(**vars(opts))
        # Publish should crash
        self.client.publish = None

    def test_reset(self, stdout):
        """Test reset errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: reset ARCHI NUM\n'
               '  ARCHI: m3/a8\n'
               '  NUM:   node num\n')

        # Missing port
        self.client.onecmd('reset m3')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid port
        self.client.onecmd('reset m3 abc')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('reset m3 123 anotherone')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_poweron(self, stdout):
        """Test poweron errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: poweron ARCHI NUM\n'
               '  ARCHI: m3/a8\n'
               '  NUM:   node num\n')

        # Missing port
        self.client.onecmd('poweron m3')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid port
        self.client.onecmd('poweron m3 abc')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('poweron m3 123 anotherone')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_poweroff(self, stdout):
        """Test poweroff errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: poweroff ARCHI NUM\n'
               '  ARCHI: m3/a8\n'
               '  NUM:   node num\n')

        # Missing port
        self.client.onecmd('poweroff m3')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid port
        self.client.onecmd('poweroff m3 abc')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('poweroff m3 123 anotherone')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_update(self, stdout):
        """Test update errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: update ARCHI NUM FIRMWAREPATH\n'
               '  ARCHI: m3/a8\n'
               '  NUM:   node num\n'
               '  FIRMWAREPATH: Path to the firmware.\n'
               '                Idle firmware if not provided\n')

        # Missing port
        self.client.onecmd('update m3')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid port
        self.client.onecmd('update m3 abc')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid file path
        self.client.onecmd('update m3 1 /non/existing/path/fw.elf')
        err = ("Could not open file: [Errno 2] No such file or directory: "
               "'/non/existing/path/fw.elf'\n")
        self.assertEqual(stdout.getvalue(), err + hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        cmd = 'update m3 123 %s anotherone' % os.devnull
        self.client.onecmd(cmd)
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)
