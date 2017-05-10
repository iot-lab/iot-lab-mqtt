# -*- coding:utf-8 -*-
"""Integration tests for IoT-LAB MQTT serial client and server."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import contextlib
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import mock

from iotlabmqtt import serial
from iotlabmqtt.clients import serial as serial_client

from . import IntegrationTestCase
from .. import TestCaseImproved


class SerialIntegrationTest(IntegrationTestCase):
    """Test serial client and server using a broker."""

    def setUp(self):
        super().setUp()
        for port in range(20001, 20003):
            self.socat_start(port)

    def tearDown(self):
        for port in list(self.socat):
            self.socat_stop(port)

    @staticmethod
    @contextlib.contextmanager
    def start_client_and_server(brokerport):
        """Start serial client and server context manager.

        Yields client and stdout mock.
        """
        args = ['localhost', '--broker-port', '%s' % brokerport,
                '--prefix', 'serial/test/prefix']
        opts = serial.PARSER.parse_args(args)
        server = serial.MQTTAggregator.from_opts_dict(**vars(opts))
        server.start()

        try:
            args = ['localhost', '--broker-port', '%s' % brokerport,
                    '--prefix', 'serial/test/prefix',
                    '--site', server.HOSTNAME]
            opts = serial_client.PARSER.parse_args(args)
            client = serial_client.SerialShell.from_opts_dict(**vars(opts))
            client.start()

            try:
                with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
                    yield client, stdout
            finally:
                client.stop()
        finally:
            server.stop()

    def test_serial_agent_one_node(self):
        """Test serial agent normal cases."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_serial_agent_one_node(client, stdout)

    def _test_serial_agent_one_node(self, client, stdout):
        port = 20001
        soc = self.socat[port]

        # Write non nonnected line
        first = 'err_not_conn'
        client.onecmd('linewrite localhost %u %s' % (port, first))

        err = ('SERIAL ERROR: localhost/20001/line/data/in: '
               'Non connected node localhost-20001\n'
               '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, err, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # Start line
        client.onecmd('linestart localhost %u' % port)

        # Start line again
        client.onecmd('linestart localhost %u' % port)

        # No message == success for both
        self.assertEqual(stdout.getvalue(), '')

        # Write to node
        second = 'wrïttén'
        client.onecmd('linewrite localhost %u %s' % (port, second))

        out = soc.stdout.read(len((second + '\n').encode('utf-8')))
        self.assertEqual(out, (second + '\n').encode('utf-8'))

        # Node answers
        second_ret = 'ánßwër'
        soc.stdin.write((second_ret + '\n').encode('utf-8'))
        soc.stdin.flush()

        answer = ('line_handler(localhost-20001): ánßwër\n'
                  '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, answer, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # Node sends not utf-8 data
        invalid_bytes = b'this: \xc3\x28 is invalid\n'
        soc.stdin.write(invalid_bytes)
        soc.stdin.flush()

        answer = ('line_handler(localhost-20001): this: �( is invalid\n'
                  '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, answer, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # Stop node
        client.onecmd('stop localhost %u' % port)
        self.assertEqual(stdout.getvalue(), '')
        stdout.seek(0)
        stdout.truncate(0)

        # Correctly stopped
        third = 'err_stopped'
        client.onecmd('linewrite localhost %u %s' % (port, third))

        err = ('SERIAL ERROR: localhost/20001/line/data/in: '
               'Non connected node localhost-20001\n'
               '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, err, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # Can stop another time without error
        client.onecmd('stop localhost %u' % port)
        self.assertEqual(stdout.getvalue(), '')

        # Stop all nodes (but no nodes in fact)
        client.onecmd('stopall')
        self.assertEqual(stdout.getvalue(), '')

    def test_serial_agent_no_port(self):
        """Test connecting on non connected node."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_serial_agent_no_port(client, stdout)

    def _test_serial_agent_no_port(self, client, stdout):
        port = 20000
        assert port not in self.socat, "port 20000 is used"

        # Start line non existing node
        client.onecmd('linestart localhost %u' % port)

        # Error message
        err = 'Connection failed: [Errno 111] Connection refused\n'
        self.assertEqual(stdout.getvalue(), err)
        stdout.seek(0)
        stdout.truncate(0)

    def test_serial_agent_dns_fail(self):
        """Test connecting on non existing dns node."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_serial_agent_dns_fail(client, stdout)

    def _test_serial_agent_dns_fail(self, client, stdout):
        """This dns error is raised directly by connect.

        So it triggers a different path than an async failure.
        """

        # Start line non existing dns entry (even on IoT-LAB, raises DNS fail)
        client.onecmd('linestart m3 1234')

        # Error message
        error_start = 'Connection failed: [Errno -'
        # -5] No address associated with hostname')
        # got a different message on ArchLinux
        # -2] Name or service not known
        self.assertTrue(stdout.getvalue().startswith(error_start))
        stdout.seek(0)
        stdout.truncate(0)

    def test_serial_agent_conn_stop(self):
        """Connection stops on one node, and stopall."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_serial_agent_conn_stop(client, stdout)

    def _test_serial_agent_conn_stop(self, client, stdout):
        port = 20001

        for port in self.socat:
            # Start line
            client.onecmd('linestart localhost %u' % port)
        self.assertEqual(stdout.getvalue(), '')

        # Break connection and error from disconnect
        self.socat_stop(port)

        err = ('SERIAL ERROR: localhost/20002: '
               'Connection closed in state line\n'
               '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, err, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # Restart socat
        self.socat_start(port)

        # Stop all nodes with nodes
        client.onecmd('stopall')
        self.assertEqual(stdout.getvalue(), '')


@mock.patch('sys.stdout', new_callable=StringIO)
class SerialClientErrorTests(TestCaseImproved):
    """Test SerialClient Parsing errors."""
    def setUp(self):
        args = ['localhost', '--broker-port', '%s' % 54321,
                '--prefix', 'serial/test/prefix',
                '--site', serial.MQTTAggregator.HOSTNAME]
        opts = serial_client.PARSER.parse_args(args)
        self.client = serial_client.SerialShell.from_opts_dict(**vars(opts))
        # Publish should crash
        self.client.publish = None

    def test_linestart(self, stdout):
        """Test linestart parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: linestart ARCHI NUM\n'
               '  ARCHI: m3/a8\n'
               '  NUM:   node num\n')

        # Missing port
        self.client.onecmd('linestart localhost')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid port
        self.client.onecmd('linestart localhost abc')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('linestart localhost 123 haha')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_stop(self, stdout):
        """Test stop parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: stop ARCHI NUM\n'
               '  ARCHI: m3/a8\n'
               '  NUM:   node num\n')

        # Missing port
        self.client.onecmd('stop localhost')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid port
        self.client.onecmd('stop localhost abc')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('stop localhost 123 haha')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_linewrite(self, stdout):
        """Test linewrite parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: linewrite ARCHI NUM MESSAGE\n'
               '  ARCHI: m3/a8\n'
               '  NUM:   node num\n'
               '  MESSAGE: Message line to send\n')

        # Missing message
        self.client.onecmd('linewrite localhost 123')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid port
        self.client.onecmd('linewrite localhost abc message')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_stopall(self, stdout):
        """Test stopall help."""
        hlp = 'stopall\n'

        # cannot be done from command, just call it
        self.client.onecmd('help stopall')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)
