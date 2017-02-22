# -*- coding:utf-8 -*-
"""Integration tests for IoT-LAB MQTT serial client and server."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
import subprocess

import mock

from iotlabmqtt import serial
from iotlabmqtt.clients import serial as serial_client

from . import IntegrationTestCase


class SerialIntegrationTest(IntegrationTestCase):
    """Test serial client and server using a broker."""

    def setUp(self):
        self.socat = {}
        for port in range(20001, 20003):
            self.socat_start(port)

    def tearDown(self):
        for port in list(self.socat):
            self.socat_stop(port)

    def socat_start(self, port, wait=1):
        """Register new socat on ``port``."""
        self.socat[port] = self._socat_start(port, wait)

    def socat_stop(self, port):
        """Close socat on ``port``."""
        soc = self.socat.pop(port)
        soc.terminate()
        soc.wait()

    @staticmethod
    def _socat_start(port, wait=1):
        """Start socat on ``port``.

        :param port: socat listening port
        :param wait: waiting time after starting process to check if running
        """
        tcp_listen = 'tcp4-listen:{port},reuseaddr,fork'.format(port=port)
        cmd = ['socat', '-', tcp_listen]
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE)
        time.sleep(wait)
        if proc.poll() is not None:
            raise ValueError('Failed starting socat {}'.format(port))

        return proc

    @mock.patch('iotlabmqtt.clients.serial.print')
    def test_serial_agents(self, serial_print):
        """Test serial agents."""
        args = ['localhost', '--broker-port', '%s' % self.BROKERPORT,
                '--prefix', 'serial/test/prefix']
        opts = serial.PARSER.parse_args(args)
        server = serial.MQTTAggregator.from_opts_dict(**vars(opts))
        server.start()

        try:
            args = ['localhost', '--broker-port', '%s' % self.BROKERPORT,
                    '--prefix', 'serial/test/prefix',
                    '--site', serial.MQTTAggregator.HOSTNAME]
            opts = serial_client.PARSER.parse_args(args)
            client = serial_client.SerialShell.from_opts_dict(**vars(opts))
            client.start()

            try:
                self._test_serial_agent_one_node(client, serial_print)
                self._test_serial_agent_no_port(client, serial_print)
                self._test_serial_agent_conn_stop(client, serial_print)
            finally:
                client.stop()
        finally:
            server.stop()

    def _test_serial_agent_one_node(self, client, serial_print):
        """Test serial agent normal cases."""

        port = 20001
        soc = self.socat[port]

        # Write non nonnected line
        first = 'err_not_conn'
        client.onecmd('linewrite localhost %u %s' % (port, first))

        err = [mock.call('SERIAL ERROR: localhost/20001/line/data/in: '
                         'Non connected node localhost-20001')]
        self.assertEqualTimeout(lambda: serial_print.call_args_list, err, 2)
        serial_print.reset_mock()

        # Start line
        client.onecmd('linestart localhost %u' % port)

        # Start line again
        client.onecmd('linestart localhost %u' % port)

        # No message == success for both
        self.assertEqual(serial_print.call_args_list, [])

        # Write to node
        second = 'wrïttén'
        client.onecmd('linewrite localhost %u %s' % (port, second))

        out = soc.stdout.read(len((second + '\n').encode('utf-8')))
        self.assertEqual(out, (second + '\n').encode('utf-8'))

        # Node answers
        second_ret = 'ánßwër'
        soc.stdin.write((second_ret + '\n').encode('utf-8'))
        soc.stdin.flush()

        answer = [mock.call('line_handler(localhost-20001): ánßwër')]
        self.assertEqualTimeout(lambda: serial_print.call_args_list, answer, 2)
        serial_print.reset_mock()

        # Stop node
        client.onecmd('stop localhost %u' % port)
        self.assertEqual(serial_print.call_args_list, [])

        # Correctly stopped
        third = 'err_stopped'
        client.onecmd('linewrite localhost %u %s' % (port, third))

        err = [mock.call('SERIAL ERROR: localhost/20001/line/data/in: '
                         'Non connected node localhost-20001')]
        self.assertEqualTimeout(lambda: serial_print.call_args_list, err, 2)
        serial_print.reset_mock()

        # Can stop another time without error
        client.onecmd('stop localhost %u' % port)
        self.assertEqual(serial_print.call_args_list, [])

        # Stop all nodes (but no nodes in fact)
        client.onecmd('stopall')
        self.assertEqual(serial_print.call_args_list, [])

    def _test_serial_agent_no_port(self, client, serial_print):
        """Test connecting on non connected node."""
        port = 20000
        assert port not in self.socat, "port 20000 is used"

        # Start line non existing node
        client.onecmd('linestart localhost %u' % port)

        # Error message
        err = [mock.call(u'Connection failed: [Errno 111] Connection refused')]
        self.assertEqual(serial_print.call_args_list, err)
        serial_print.reset_mock()

    def _test_serial_agent_conn_stop(self, client, serial_print):
        """Connection stops on one node, and stopall."""
        port = 20001

        for port in self.socat:
            # Start line
            client.onecmd('linestart localhost %u' % port)
        self.assertEqual(serial_print.call_args_list, [])

        # Break connection and error from disconnect
        self.socat_stop(port)
        err = [mock.call(u'SERIAL ERROR: localhost/20002: Connection closed')]
        self.assertEqualTimeout(lambda: serial_print.call_args_list, err, 2)
        serial_print.reset_mock()
        # Restart socat
        self.socat_start(port)

        # Stop all nodes with nodes
        client.onecmd('stopall')
        self.assertEqual(serial_print.call_args_list, [])
