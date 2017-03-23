# -*- coding:utf-8 -*-
"""Integration tests for IoT-LAB MQTT radiosniffer client and server."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os
import time
import contextlib
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import mock

from iotlabmqtt import radiosniffer
from iotlabmqtt.clients import radiosniffer as radiosniffer_client

from . import IntegrationTestCase
from .. import TestCaseImproved

# pylint:disable=invalid-name


def generate_zep_packet():
    """Generate a zep packet."""

    import binascii
    zep_msg = (
        '45 58 02 01'   # Base Zep header
        '0B 00 01 00 ff'   # chan | dev_id | dev_id| LQI/CRC_MODE |  LQI

        '83 aa 7e 80'   # Timestamp msb (Epoch 1/1/1970)
        '00 00 00 00'   # timestamp lsp

        '00 00 00 01'   # seqno

        '00 01 02 03'   # reserved 0-3/10
        '04 05 16 07'   # reserved 4-7/10
        '08 09'         # reserved 8-9 / 10
        '08'            # Length 2 + data_len
        '61 62 63'      # Data
        '41 42 43'      # Data
        'FF FF'         # CRC)
    )
    zep_msg = zep_msg.replace(' ', '')
    return binascii.a2b_hex(zep_msg)


class RadioSnifferIntegrationTest(IntegrationTestCase):
    """Test sniffer client and server using a broker."""

    def setUp(self):
        self.socat = {}
        for port in range(30001, 30003):
            self.socat_start(port)

    def tearDown(self):
        for port in list(self.socat):
            self.socat_stop(port)

    @contextlib.contextmanager
    def start_client_and_server(self, brokerport):
        """Start radiosiffer client and server context manager.

        Yields client and stdout mock.
        """
        # pylint:disable=attribute-defined-outside-init
        args = ['localhost', '--broker-port', '%s' % brokerport,
                '--prefix', 'radiosniffer/test/prefix']
        args += ['--experiment-id', '12345',
                 '--iotlab-user', 'us3rn4me',
                 '--iotlab-password', 'p4sswd']
        opts = radiosniffer.PARSER.parse_args(args)

        with mock.patch('iotlabcli.experiment.get_experiment') as get_exp:
            get_exp.return_value = {'state': 'Running'}

            server = radiosniffer.MQTTRadioSnifferAggregator.from_opts_dict(
                **vars(opts))

        assert server.iotlabapi.expid == 12345
        assert server.iotlabapi.api.auth.username == 'us3rn4me'
        assert server.iotlabapi.api.auth.password == 'p4sswd'
        server.iotlabapi.api = None  # Breaks on calls

        server.start()
        self.server = server

        try:
            args = ['localhost', '--broker-port', '%s' % brokerport,
                    '--prefix', 'radiosniffer/test/prefix',
                    '--site', server.HOSTNAME]
            opts = radiosniffer_client.PARSER.parse_args(args)
            client = radiosniffer_client.RadioSnifferShell.from_opts_dict(
                **vars(opts))
            client.start()

            try:
                with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
                    yield client, stdout
            finally:
                client.stop()
        finally:
            server.stop()

    def test_radiosniffer_agent_one_node(self):
        """Test radiosniffer agent normal case."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_radiosniffer_agent_one_node(client, stdout)

    def _test_radiosniffer_agent_one_node(self, client, stdout):
        """Simple check one node sniffer.

        Global header, start, 4 packets, stop, close pcap file.
        """
        self.server.iotlabapi.set_sniffer_channel = mock.Mock()

        port = 30001
        soc = self.socat[port]
        channel = 11
        outpcap = '/tmp/test.pcap'

        # Init Global pcap
        client.onecmd('rawpcap %s' % outpcap)
        out = 'Writing RAW PCAP header: 24 bytes\n'
        self.assertEqual(stdout.getvalue(), out)
        stdout.seek(0)
        stdout.truncate(0)

        # Start sniffer raw
        self.server.iotlabapi.set_sniffer_channel.return_value = {'30001': ''}

        client.onecmd('rawstart localhost %u %u' % (port, channel))
        self.server.iotlabapi.set_sniffer_channel.assert_called_with(
            channel, 'localhost', '30001')
        self.assertEqual(stdout.getvalue(), '')

        # Send 4 packets
        soc.stdin.write(generate_zep_packet())
        soc.stdin.write(generate_zep_packet())
        soc.stdin.write(generate_zep_packet())
        soc.stdin.write(generate_zep_packet())
        soc.stdin.flush()

        answer = ('raw_handler(localhost-30001): PKT: len(24)\n'
                  '(Cmd) raw_handler(localhost-30001): PKT: len(24)\n'
                  '(Cmd) raw_handler(localhost-30001): PKT: len(24)\n'
                  '(Cmd) raw_handler(localhost-30001): PKT: len(24)\n'
                  '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, answer, 5)
        stdout.seek(0)
        stdout.truncate(0)

        # Stop when running
        client.onecmd('stop localhost %u' % port)
        self.assertEqual(stdout.getvalue(), '')

        # Close packet
        client.onecmd('rawpcapclose')
        self.assertEqual(stdout.getvalue(), '')

        # outfile only has global header in it
        self.assertEqual(os.stat(outpcap).st_size, 24 + 4 * 24)

    def test_radiosniffer_agent_one_node_complex(self):
        """Test radiosniffer agent complex cases."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_radiosniffer_agent_one_node_complex(client, stdout)

    def _test_radiosniffer_agent_one_node_complex(self, client, stdout):
        """Wrong order start/stop sending messages without an output file."""
        self.server.iotlabapi.set_sniffer_channel = mock.Mock()

        port = 30001
        soc = self.socat[port]
        channel = 11
        outpcap = '/tmp/test.pcap'

        # Stop for nothing
        client.onecmd('stop localhost %u' % port)
        self.assertEqual(stdout.getvalue(), '')

        # Stopall for nothing
        client.onecmd('stopall')
        self.assertEqual(stdout.getvalue(), '')

        # Init Global pcap
        client.onecmd('rawpcap %s' % outpcap)
        out = 'Writing RAW PCAP header: 24 bytes\n'
        self.assertEqual(stdout.getvalue(), out)
        stdout.seek(0)
        stdout.truncate(0)

        # Close packet
        client.onecmd('rawpcapclose')
        self.assertEqual(stdout.getvalue(), '')

        # Start sniffer raw
        self.server.iotlabapi.set_sniffer_channel.return_value = {'30001': ''}
        client.onecmd('rawstart localhost %u %u' % (port, channel))
        self.server.iotlabapi.set_sniffer_channel.assert_called_with(
            channel, 'localhost', '30001')
        self.assertEqual(stdout.getvalue(), '')

        # Start sniffer raw again
        client.onecmd('rawstart localhost %u %u' % (port, channel))
        err = 'Already started, stop before start to change channel\n'
        self.assertEqual(stdout.getvalue(), err)
        stdout.seek(0)
        stdout.truncate(0)

        # Send 3 packets
        # First packet split before full length to execute the code handling
        # this
        pkt = generate_zep_packet()
        soc.stdin.write(pkt[:-2])
        soc.stdin.flush()
        time.sleep(1)  # wait for the packet to be handled
        soc.stdin.write(pkt[-2:])
        soc.stdin.flush()

        # Two packets full
        soc.stdin.write(generate_zep_packet())
        soc.stdin.write(generate_zep_packet())
        soc.stdin.flush()

        answer = ('raw_handler(localhost-30001): PKT: len(24)\n'
                  '(Cmd) raw_handler(localhost-30001): PKT: len(24)\n'
                  '(Cmd) raw_handler(localhost-30001): PKT: len(24)\n'
                  '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, answer, 5)
        stdout.seek(0)
        stdout.truncate(0)

        # Stop when running
        client.onecmd('stop localhost %u' % port)
        self.assertEqual(stdout.getvalue(), '')

        # outfile only has global header in it
        self.assertEqual(os.stat(outpcap).st_size, 24)

    def test_radiosniffer_agent_invalid_cases(self):
        """Test radiosniffer agent invalid cases."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_radiosniffer_agent_invalid_cases(client, stdout)

    def _test_radiosniffer_agent_invalid_cases(self, client, stdout):
        port = 30001

        # Start sniffer raw invalid channel
        client.onecmd('rawstart localhost %u %u' % (port, 42))
        error = 'Invalid channel value, should be in [11, 26]\n'
        self.assertEqual(stdout.getvalue(), error)
        stdout.seek(0)
        stdout.truncate(0)

    def test_radiosniffer_agent_sniffer_fail(self):
        """Test radiosniffer agent sniffer set fail."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_radiosniffer_agent_sniffer_fail(client, stdout)

    def _test_radiosniffer_agent_sniffer_fail(self, client, stdout):
        """Check setting sniffer but fails."""
        self.server.iotlabapi.set_sniffer_channel = mock.Mock()

        # Start sniffer raw
        self.server.iotlabapi.set_sniffer_channel.return_value = {
            '30001': 'Update profile failed: error string'}

        client.onecmd('rawstart localhost %u %u' % (30001, 11))
        self.server.iotlabapi.set_sniffer_channel.assert_called_with(
            11, 'localhost', '30001')
        err = 'Update profile failed: error string\n'
        self.assertEqual(stdout.getvalue(), err)
        stdout.seek(0)
        stdout.truncate(0)

        # Start sniffer but connection fails
        assert 30000 not in self.socat, 'port 30000 is used'
        self.server.iotlabapi.set_sniffer_channel.return_value = {'30000': ''}
        client.onecmd('rawstart localhost %u %u' % (30000, 26))
        self.server.iotlabapi.set_sniffer_channel.assert_called_with(
            26, 'localhost', '30000')
        err = 'Connection failed: [Errno 111] Connection refused\n'
        self.assertEqual(stdout.getvalue(), err)
        stdout.seek(0)
        stdout.truncate(0)

    def test_radiosniffer_agent_sniffer_disconnect(self):
        """Test radiosniffer agent sniffer disconnection."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_radiosniffer_agent_sniffer_disconnect(client, stdout)

    def _test_radiosniffer_agent_sniffer_disconnect(self, client, stdout):
        """Check setting sniffer but fails."""
        # Don't mock set_sniffer_channel, should work for localhost
        port = 30001
        channel = 11

        # Start sniffer and connection breaks
        client.onecmd('rawstart localhost %u %u' % (port, channel))
        self.assertEqual(stdout.getvalue(), '')

        # Stop conn
        time.sleep(1)
        self.socat_stop(port)

        # Error raised
        err = ('RADIO SNIFFER ERROR: localhost/30001: '
               'Connection closed in state raw\n'
               '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, err, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # Restart socat
        self.socat_start(port)

    def test_radiosniffer_agent_sniffer_fail_m3_a8(self):
        """Test radiosniffer agent sniffer connection failed for m3/a8."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_radiosniffer_agent_sniffer_fail_m3_a8(client, stdout)

    def _test_radiosniffer_agent_sniffer_fail_m3_a8(self, client, stdout):
        """Check setting sniffer but fails for connectiong m3/a8.

        Mock iotlabapi at low level to try the whole integration.
        I want to increase the chances for it to work
        """
        # Low level api mock
        self.server.iotlabapi.api = mock.Mock()
        api = self.server.iotlabapi.api
        site = self.server.iotlabapi.site

        # M3-1234 channel 11
        api.add_profile.return_value = {'create': 'iotlabmqtt_11_m3'}
        api.node_command.return_value = {
            '0': ['m3-1234.%s.iot-lab.info' % site],
        }

        # Start sniffer but connection fails
        client.onecmd('rawstart m3 1234 11')
        error_start = 'Connection failed: [Errno -'
        # -5] No address associated with hostname')
        # got a different message on ArchLinux
        # -2] Name or service not known
        self.assertTrue(stdout.getvalue().startswith(error_start))
        stdout.seek(0)
        stdout.truncate(0)

        # Verify add_profile call
        name, profile = api.add_profile.call_args[0]
        self.assertEqual(name, 'iotlabmqtt_11_m3')
        self.assertEqual(profile.nodearch, 'm3')
        self.assertEqual(profile.radio['mode'], 'sniffer')
        self.assertEqual(profile.radio['channels'], [11])

        # Verify node_command call
        api.node_command.assert_called_with(
            'profile', self.server.iotlabapi.expid,
            ['m3-1234.%s.iot-lab.info' % site], '&name=iotlabmqtt_11_m3')

        # Test A8
        api.add_profile.return_value = {'create': 'iotlabmqtt_11_a8'}
        api.node_command.return_value = {
            '0': ['a8-1234.%s.iot-lab.info' % site],
        }
        # Start sniffer on a8 but connection fails
        client.onecmd('rawstart a8 1234 11')
        error_start = 'Connection failed: [Errno -'
        # -5] No address associated with hostname')
        # got a different message on ArchLinux
        # -2] Name or service not known
        self.assertTrue(stdout.getvalue().startswith(error_start))
        stdout.seek(0)
        stdout.truncate(0)


@mock.patch('sys.stdout', new_callable=StringIO)
class RadioSnifferClientErrorTests(TestCaseImproved):
    """Test RadioSniffer parsing errors."""
    def setUp(self):
        args = ['localhost', '--broker-port', '%s' % 54321,
                '--prefix', 'radiosniffer/test/prefix',
                '--site', radiosniffer.MQTTRadioSnifferAggregator.HOSTNAME]
        opts = radiosniffer_client.PARSER.parse_args(args)
        self.client = radiosniffer_client.RadioSnifferShell.from_opts_dict(
            **vars(opts))
        # Publish should crash
        self.client.publish = None

    def test_rawpcap(self, stdout):
        """Test rawpcap errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: rawpcap FILEPATH\n'
               '  FILEPATH: rawpcap output\n')

        # No file
        self.client.onecmd('rawpcap')
        err = "Could not open file: [Errno 2] No such file or directory: ''\n"
        self.assertEqual(stdout.getvalue(), err + hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Cannot open file
        self.client.onecmd('rawpcap /non_existing/dir/and/file')
        err = ("Could not open file: [Errno 2] No such file or directory: "
               "'/non_existing/dir/and/file'\n")
        self.assertEqual(stdout.getvalue(), err + hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_rawpcapclose(self, stdout):
        """Test rawpcapclose help."""
        hlp = ('rawpcapclose\n'
               '  Close the current rawpcap file\n')

        # cannot be done from command, just call it
        self.client.onecmd('help rawpcapclose')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_rawstart(self, stdout):
        """Test rawstart parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: rawstart ARCHI NUM CHANNEL\n'
               '  ARCHI:   m3/a8\n'
               '  NUM:     node num\n'
               '  CHANNEL: sniffer channel\n')

        # Missing port
        self.client.onecmd('rawstart localhost')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid port
        self.client.onecmd('rawstart localhost abc')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid channel
        self.client.onecmd('rawstart m3 123 CHANNEL')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('rawstart m3 123 11 anotherone')
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

    def test_stopall(self, stdout):
        """Test stopall help."""
        hlp = 'stopall\n'

        # cannot be done from command, just call it
        self.client.onecmd('help stopall')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)
