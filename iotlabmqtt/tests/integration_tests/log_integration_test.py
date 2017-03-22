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
from iotlabmqtt.clients import log as log_client

from . import IntegrationTestCase
from .. import TestCaseImproved


class LogIntegrationTest(IntegrationTestCase):
    """Test log client using a broker."""
    def setUp(self):
        self.prefix = 'log/test/prefix'
        self.timestamp = None
        self.client = None
        self.client_log_handler = None

    @contextlib.contextmanager
    def start_client(self, brokerport):
        """Start log client context manager.

        Yields client and stdout mock.
        """
        args = ['localhost', '--broker-port', '%s' % brokerport,
                '--prefix', self.prefix]
        opts = log_client.PARSER.parse_args(args)

        self.client_log_handler = log_client.LogShell.log_handler
        with mock.patch.object(log_client.LogShell, 'log_handler',
                               self._log_handler):
            self.client = log_client.LogShell.from_opts_dict(**vars(opts))
        self.client.start()

        try:
            with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
                yield self.client, stdout
        finally:
            self.client.stop()

    def _log_handler(self, message):
        message.timestamp = self.timestamp
        self.client_log_handler(self.client, message)

    def _topic(self, topic):
        return os.path.join(self.prefix, topic)

    def test_log(self):
        """Test log cases."""
        with self.start_client(self.BROKERPORT) as (client, stdout):
            self._test_log(client, stdout)

    def _test_log(self, client, stdout):
        # Null
        self.timestamp = 1492008169.880
        message = (
            "1492008169.880 log/test/prefix/a/b/c ''\n"
            "(Cmd) "
        )
        client.client.publish(self._topic('a/b/c'), None)
        self.assertEqualTimeout(stdout.getvalue, message, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # Null
        self.timestamp = 1492008946.123
        message = (
            "1492008946.123 log/test/prefix/null/b/c ''\n"
            "(Cmd) "
        )
        client.client.publish(self._topic('null/b/c'), b'')
        self.assertEqualTimeout(stdout.getvalue, message, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # UTF8
        self.timestamp = 1492009044.880
        message = (
            "1492009044.880 log/test/prefix/u/ni/code 'Gaëtan'\n"
            "(Cmd) "
        )
        client.client.publish(self._topic('u/ni/code'),
                              'Gaëtan'.encode('utf-8'))
        self.assertEqualTimeout(stdout.getvalue, message, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # bytes
        payload = bytearray(range(256))
        self.timestamp = 1492009308.999
        message = (
            "1492009308.999 log/test/prefix/b/ytes "
            "'BIN: (len 256): hash: 4916d6'\n"
            "(Cmd) "
        )
        client.client.publish(self._topic('b/ytes'), payload)
        self.assertEqualTimeout(stdout.getvalue, message, 2)
        stdout.seek(0)
        stdout.truncate(0)

    def test_log_and_outfile(self):
        """Test log cases with outfile."""
        with self.start_client(self.BROKERPORT) as (client, stdout):
            self._test_log_and_outfile(client, stdout)

    def _test_log_and_outfile(self, client, stdout):

        outfile = '/tmp/outlog'
        # Reuse _test_log to produce output

        # Nothing saved
        self._test_log(client, stdout)

        client.onecmd('open %s' % outfile)
        self._test_log(client, stdout)

        # Trim file and re-save
        client.onecmd('open %s' % outfile)
        self._test_log(client, stdout)

        # Close and no output save after
        client.onecmd('close')
        self._test_log(client, stdout)

        # Only one time
        output = open(outfile).read()
        expected = (
            '1492008169.880;log/test/prefix/a/b/c;\n'
            '1492008946.123;log/test/prefix/null/b/c;\n'
            '1492009044.880;log/test/prefix/u/ni/code;R2HDq3Rhbg==\n'
            '1492009308.999;log/test/prefix/b/ytes;'

            'AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vM'
            'DEyMzQ1Njc4OTo7PD0+P0BBQkNERUZHSElKS0xNTk9QUVJTVFVWV1hZWltcXV5fYG'
            'FiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6e3x9fn+AgYKDhIWGh4iJiouMjY6PkJG'
            'Sk5SVlpeYmZqbnJ2en6ChoqOkpaanqKmqq6ytrq+wsbKztLW2t7i5uru8vb6/wMHC'
            'w8TFxsfIycrLzM3Oz9DR0tPU1dbX2Nna29zd3t/g4eLj5OXm5+jp6uvs7e7v8PHy8'
            '/T19vf4+fr7/P3+/w==\n'
        )

        self.assertEqual(output, expected)

        os.remove(outfile)


@mock.patch('sys.stdout', new_callable=StringIO)
class LogClientErrorTests(TestCaseImproved):
    """Test Log parsing errors."""

    def setUp(self):
        args = ['localhost', '--broker-port', '%s' % 54321,
                '--prefix', 'log/test/prefix']
        opts = log_client.PARSER.parse_args(args)
        self.client = log_client.LogShell.from_opts_dict(**vars(opts))
        # Publish should crash
        self.client.publish = None

    def test_open(self, stdout):
        """Test open errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: open LOGFILE\n'
               '  LOGFILE:   csv log file\n')

        self.client.onecmd('open')
        err = "Could not open file: [Errno 2] No such file or directory: ''\n"
        self.assertEqual(stdout.getvalue(), err + hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Cannot open file
        self.client.onecmd('open /non_existing/dir/and/file')
        err = ("Could not open file: [Errno 2] No such file or directory: "
               "'/non_existing/dir/and/file'\n")
        self.assertEqual(stdout.getvalue(), err + hlp)
        stdout.seek(0)

    def test_close(self, stdout):
        """Test close help."""
        hlp = ('close\n'
               '  Close current logfile\n')

        # cannot be done from command, just call it
        self.client.onecmd('help close')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)
