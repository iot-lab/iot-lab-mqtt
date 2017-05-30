# -*- coding:utf-8 -*-
"""Integration tests for IoT-LAB MQTT process client and server."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import time
import contextlib

import mock

from iotlabmqtt import process
from iotlabmqtt.clients import process as process_client

from . import IntegrationTestCase
from .. import TestCaseImproved

# pylint:disable=invalid-name

PROC_END_FMT = (
    "stderr({procid}): ''\n"
    "(Cmd) stdout({procid}): ''\n"
    "(Cmd) closed({procid}): {ret}\n"
    "(Cmd) "
)


class ProcessIntegrationTests(IntegrationTestCase):
    """Test process client and server using a broker."""

    @contextlib.contextmanager
    def start_client_and_server(self, brokerport):
        """Start process client and server context manager.

        Yields client and stdout mock.
        """
        # pylint:disable=attribute-defined-outside-init
        args = ['localhost', '--broker-port', '%s' % brokerport,
                '--prefix', 'process/test/prefix']
        opts = process.PARSER.parse_args(args)
        server = process.MQTTProcessAgent.from_opts_dict(**vars(opts))
        server.start()
        self.server = server
        try:
            args = ['localhost', '--broker-port', '%s' % brokerport,
                    '--prefix', 'process/test/prefix',
                    '--site', server.HOSTNAME]
            opts = process_client.PARSER.parse_args(args)
            client = process_client.ProcessShell.from_opts_dict(**vars(opts))
            client.start()

            try:
                with mock.patch('sys.stdout', new_callable=StringIO) as stdout:
                    yield client, stdout
            finally:
                client.stop()
        finally:
            server.stop()

    def test_process_agent_new_free_list(self):
        """Test process agent new, free and list."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_new_free_list(client, stdout)

    def _test_process_agent_new_free_list(self, client, stdout):
        """Test process agent new, free and list.

        Play with allocation and release.
        """
        # pylint:disable=too-many-statements

        client.onecmd('list')
        self.assertEqual(stdout.getvalue(), '[]\n')
        stdout.seek(0)
        stdout.truncate(0)

        # Create two processes
        client.onecmd('new')
        self.assertEqual(stdout.getvalue(), '1\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('new procname')
        self.assertEqual(stdout.getvalue(), 'procname\n')
        stdout.seek(0)
        stdout.truncate(0)

        # Already used
        client.onecmd('new procname')
        self.assertEqual(stdout.getvalue(), 'name procname already in use\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('list')
        self.assertEqual(stdout.getvalue(), "['1', 'procname']\n")
        stdout.seek(0)
        stdout.truncate(0)

        # Two free on same name
        client.onecmd('free 1')
        self.assertEqual(stdout.getvalue(), '')

        client.onecmd('free 1')
        self.assertEqual(stdout.getvalue(), 'Name 1 not found\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('list')
        self.assertEqual(stdout.getvalue(), "['procname']\n")
        stdout.seek(0)
        stdout.truncate(0)

        # Create manually '2'
        # Then new will create 3 as 2 already exists
        client.onecmd('new 2')
        self.assertEqual(stdout.getvalue(), '2\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('new')
        self.assertEqual(stdout.getvalue(), '3\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('list')
        self.assertEqual(stdout.getvalue(), "['2', '3', 'procname']\n")
        stdout.seek(0)
        stdout.truncate(0)

        # Free all
        client.onecmd('free 3')
        self.assertEqual(stdout.getvalue(), '')

        client.onecmd('free 2')
        self.assertEqual(stdout.getvalue(), '')

        client.onecmd('free procname')
        self.assertEqual(stdout.getvalue(), '')

        client.onecmd('list')
        self.assertEqual(stdout.getvalue(), '[]\n')
        stdout.seek(0)
        stdout.truncate(0)

    def test_process_agent_run_stdout(self):
        """Test process agent running with stdout."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_run_stdout(client, stdout)

    def _test_process_agent_run_stdout(self, client, stdout):
        """Test process agent running with stdout."""
        stdout_file = self.file_path('print_stdout.sh')
        # spaces not supported
        self.assertTrue(' ' not in stdout_file)

        # Sanity check
        client.onecmd('list')
        self.assertEqual(stdout.getvalue(), '[]\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('new')
        self.assertEqual(stdout.getvalue(), '1\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('list')
        self.assertEqual(stdout.getvalue(), "['1']\n")
        stdout.seek(0)
        stdout.truncate(0)

        # No active process on 1
        client.onecmd('stdinline 1 message')
        err = ('PROCESS ERROR: process/1: Process not running\n'
               '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, err, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # scripts runs for 2 seconds
        client.onecmd('run 1 %s %s %s' % (stdout_file, '20', '0.1'))
        messages = (
            "stdout(1): 'Message 1\\n'\n"
            "(Cmd) stdout(1): 'Message 2\\n'\n"
            "(Cmd) stdout(1): 'Message 3\\n'\n"
            "(Cmd) stdout(1): 'Message 4\\n'\n"
            "(Cmd) stdout(1): 'Message 5\\n'\n"
            "(Cmd) stdout(1): 'Message 6\\n'\n"
            "(Cmd) stdout(1): 'Message 7\\n'\n"
            "(Cmd) stdout(1): 'Message 8\\n'\n"
            "(Cmd) stdout(1): 'Message 9\\n'\n"
            "(Cmd) stdout(1): 'Message 10\\n'\n"
            "(Cmd) stdout(1): 'Message 11\\n'\n"
            "(Cmd) stdout(1): 'Message 12\\n'\n"
            "(Cmd) stdout(1): 'Message 13\\n'\n"
            "(Cmd) stdout(1): 'Message 14\\n'\n"
            "(Cmd) stdout(1): 'Message 15\\n'\n"
            "(Cmd) stdout(1): 'Message 16\\n'\n"
            "(Cmd) stdout(1): 'Message 17\\n'\n"
            "(Cmd) stdout(1): 'Message 18\\n'\n"
            "(Cmd) stdout(1): 'Message 19\\n'\n"
            "(Cmd) stdout(1): 'Message 20\\n'\n"
            "(Cmd) "
        ) + PROC_END_FMT.format(procid='1', ret='0')

        # Output may not always be ordered the same for stderr, compare sorted
        self.assertEqualTimeout(
            lambda: sorted(stdout.getvalue().splitlines(True)),
            sorted(messages.splitlines(True)),
            10)
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('poll 1')
        self.assertEqual(stdout.getvalue(), '0\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('kill 1')
        self.assertEqual(stdout.getvalue(), '')

        client.onecmd('poll 1')
        self.assertEqual(stdout.getvalue(), '0\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('free 1')
        self.assertEqual(stdout.getvalue(), '')

        client.onecmd('list')
        self.assertEqual(stdout.getvalue(), "[]\n")
        stdout.seek(0)
        stdout.truncate(0)

    def test_process_agent_run_stdin_and_stderr(self):
        """Test process agent running with sdin and stderr."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_run_stdin_and_stderr(client, stdout)

    def _test_process_agent_run_stdin_and_stderr(self, client, stdout):
        """Test process agent running with stdin and stderr."""
        stderr_file = self.file_path('echo_stderr.sh')
        # spaces not supported
        self.assertTrue(' ' not in stderr_file)

        client.onecmd('new echo')
        self.assertEqual(stdout.getvalue(), 'echo\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('run echo %s' % stderr_file)
        self.assertEqual(stdout.getvalue(), '')

        # Send messages to stdin one by one
        # first
        client.onecmd('stdinline echo first')
        messages = (
            "stderr(echo): 'first\\n'\n"
            "(Cmd) "
        )
        self.assertEqualTimeout(stdout.getvalue, messages, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # second
        client.onecmd('stdinraw echo se')
        client.onecmd('stdinraw echo co')
        client.onecmd('stdinline echo nd')
        messages = (
            "stderr(echo): 'second\\n'\n"
            "(Cmd) "
        )
        self.assertEqualTimeout(stdout.getvalue, messages, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # third
        client.onecmd('stdinline echo third')
        messages = (
            "stderr(echo): 'third\\n'\n"
            "(Cmd) "
        )
        self.assertEqualTimeout(stdout.getvalue, messages, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # Now check process running and stop it
        client.onecmd('poll echo')
        self.assertEqual(stdout.getvalue(), '')

        stdout.write('(Cmd) ')  # Add (Cmd) to help compare order
        client.onecmd('kill echo')
        # First one could be different (stdout or stderr) and this changes
        # which one has '(Cmd) '. So compare without it.
        # Output without '(Cmd) '
        output = '(Cmd) ' + PROC_END_FMT.format(procid='echo', ret='-15')
        self.assertEqualTimeout(
            lambda: sorted(stdout.getvalue().splitlines(True)),
            sorted(output.splitlines(True)), 10)
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('poll echo')
        self.assertEqual(stdout.getvalue(), '-15\n')
        stdout.seek(0)
        stdout.truncate(0)

        # Ignore messages when stopped
        client.onecmd('stdinline echo ignored message')
        time.sleep(2)
        self.assertEqual(stdout.getvalue(), '')

    def test_process_agent_dynamic_behaviour(self):
        """Test process agent running dynamic behaviour."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_dynamic_behaviour(client, stdout)

    def _test_process_agent_dynamic_behaviour(self, client, stdout):
        """Test process agent running dynamic behaviour."""
        stderr_file = self.file_path('echo_stderr.sh')
        # spaces not supported
        self.assertTrue(' ' not in stderr_file)

        client.onecmd('new 2')
        self.assertEqual(stdout.getvalue(), '2\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('run 2 %s' % stderr_file)
        self.assertEqual(stdout.getvalue(), '')

        # Invalid commands while running
        client.onecmd('free 2')
        err = 'Process still running wait or kill it first\n'
        self.assertEqual(stdout.getvalue(), err)
        stdout.seek(0)
        stdout.truncate(0)

        err_stop_first = 'Process still running, be stopped before running\n'
        client.onecmd('rerun 2')
        self.assertEqual(stdout.getvalue(), err_stop_first)
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('run 2 anything')
        self.assertEqual(stdout.getvalue(), err_stop_first)
        stdout.seek(0)
        stdout.truncate(0)

        stdout.write('(Cmd) ')  # Add (Cmd) to help compare order
        client.onecmd('kill 2')
        output = '(Cmd) ' + PROC_END_FMT.format(procid='2', ret='-15')
        self.assertEqualTimeout(
            lambda: sorted(stdout.getvalue().splitlines(True)),
            sorted(output.splitlines(True)), 10)
        stdout.seek(0)
        stdout.truncate(0)

        # Try reruning
        client.onecmd('rerun 2')
        self.assertEqual(stdout.getvalue(), '')

        client.onecmd('poll 2')
        self.assertEqual(stdout.getvalue(), '')

        stdout.write('(Cmd) ')  # Add (Cmd) to help compare order
        client.onecmd('kill 2')
        output = '(Cmd) ' + PROC_END_FMT.format(procid='2', ret='-15')
        self.assertEqualTimeout(
            lambda: sorted(stdout.getvalue().splitlines(True)),
            sorted(output.splitlines(True)), 10)
        stdout.seek(0)
        stdout.truncate(0)

    def test_process_agent_python_buffered(self):
        """Test process agent running with a python program."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_python_buffered(client, stdout)

    def _test_process_agent_python_buffered(self, client, stdout):
        """Test process agent running with a python program."""
        script_file = self.file_path('print_one_line.py')
        # spaces not supported
        self.assertTrue(' ' not in script_file)

        client.onecmd('new python')
        self.assertEqual(stdout.getvalue(), 'python\n')
        stdout.seek(0)
        stdout.truncate(0)

        # Message is received because python is run with PYTHONUNBUFFERED
        client.onecmd('run python %s' % script_file)
        messages = ("stdout(python): 'Message\\n'\n"
                    "(Cmd) ")
        self.assertEqualTimeout(stdout.getvalue, messages, 2)
        stdout.seek(0)
        stdout.truncate(0)

        # kill
        stdout.write('(Cmd) ')  # Add (Cmd) to help compare order
        client.onecmd('kill python')
        output = '(Cmd) ' + PROC_END_FMT.format(procid='python', ret='-15')
        self.assertEqualTimeout(
            lambda: sorted(stdout.getvalue().splitlines(True)),
            sorted(output.splitlines(True)), 10)
        stdout.seek(0)
        stdout.truncate(0)

    def test_process_agent_kill(self):
        """Test process agent kill cases."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_kill(client, stdout)

    def _test_process_agent_kill(self, client, stdout):
        """Test process agent kill cases."""
        trap_sigterm_file = self.file_path('trap_sigterm.sh')

        client.onecmd('new')
        self.assertEqual(stdout.getvalue(), '1\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('run 1 %s' % trap_sigterm_file)
        self.assertEqual(stdout.getvalue(), '')

        # Kill process, will be killed by SIGKILL as return value is "-9"
        stdout.write('(Cmd) ')  # Add (Cmd) to help compare order
        client.onecmd('kill 1')
        output = '(Cmd) ' + (
            "stdout(1): 'Process caught SIGTERM\\n'\n"
            "(Cmd) "
        ) + PROC_END_FMT.format(procid='1', ret='-9')
        self.assertEqualTimeout(
            lambda: sorted(stdout.getvalue().splitlines(True)),
            sorted(output.splitlines(True)), 10)
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('poll 1')
        self.assertEqual(stdout.getvalue(), '-9\n')
        stdout.seek(0)
        stdout.truncate(0)

        # Re-kill
        client.onecmd('kill 1')
        self.assertEqual(stdout.getvalue(), '')

        client.onecmd('poll 1')
        self.assertEqual(stdout.getvalue(), '-9\n')
        stdout.seek(0)
        stdout.truncate(0)

    def test_process_agent_stop_kill(self):
        """Test process agent stop that kills running processes."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_stop_kill(client, stdout)

    def _test_process_agent_stop_kill(self, client, stdout):
        """Test process agent stop that kills running processes.

        Server is stopped before client to still get messages on it.
        """
        trap_sigterm_file = self.file_path('trap_sigterm.sh')

        client.onecmd('new stop')
        self.assertEqual(stdout.getvalue(), 'stop\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('run stop %s' % trap_sigterm_file)
        self.assertEqual(stdout.getvalue(), '')

        stdout.write('(Cmd) ')  # Add (Cmd) to help compare order
        # Stop server, program should be killed by this
        self.server.stop()

        # Check process has indeed been killed
        output = '(Cmd) ' + (
            "stdout(stop): 'Process caught SIGTERM\\n'\n"
            "(Cmd) "
        ) + PROC_END_FMT.format(procid='stop', ret='-9')
        self.assertEqualTimeout(
            lambda: sorted(stdout.getvalue().splitlines(True)),
            sorted(output.splitlines(True)), 10)
        stdout.seek(0)
        stdout.truncate(0)

    def test_process_agent_not_allocated(self):
        """Test process agent when not allocated."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_not_allocated(client, stdout)

    def _test_process_agent_not_allocated(self, client, stdout):
        """Test process agent when not allocated."""

        # Non existant
        client.onecmd('poll 1')
        self.assertEqual(stdout.getvalue(), 'Name 1 not found\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('kill 1')
        self.assertEqual(stdout.getvalue(), 'Name 1 not found\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('run 1 comand')
        self.assertEqual(stdout.getvalue(), 'Name 1 not found\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('rerun 1')
        self.assertEqual(stdout.getvalue(), 'Name 1 not found\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('stdinline 1 message')
        err = ('PROCESS ERROR: process/1/fd/stdin: No process on 1\n'
               '(Cmd) ')
        self.assertEqualTimeout(stdout.getvalue, err, 2)
        stdout.seek(0)
        stdout.truncate(0)

    def test_process_agent_invalid_cases(self):
        """Test process agent running invalid cases."""
        with self.start_client_and_server(self.BROKERPORT) as (client, stdout):
            self._test_process_agent_invalid_cases(client, stdout)

    def _test_process_agent_invalid_cases(self, client, stdout):
        """Test process agent running invalid cases."""

        invalid_bytes = b'this: \xc3\x28 is invalid\n'

        # Invalid characters
        err_invalid = 'Name should not contain %s\n' % '/{}+#'
        for name in ('in/valid', 'in{val}id', 'inval+d', 'inval#d'):
            client.onecmd('new %s' % name)
            self.assertEqual(stdout.getvalue(), err_invalid)
            stdout.seek(0)
            stdout.truncate(0)

        # Invalid unicode payload
        ret = client.topics['new'].request(client.client, invalid_bytes,
                                           timeout=10, procid='1')
        self.assertEqual(ret.decode('utf-8'), 'Error decoding utf-8 payload')

        ret = client.topics['free'].request(client.client, invalid_bytes,
                                            timeout=10, procid='1')
        self.assertEqual(ret.decode('utf-8'), 'Error decoding utf-8 payload')

        # Command on non run ones
        client.onecmd('new')
        self.assertEqual(stdout.getvalue(), '1\n')
        stdout.seek(0)
        stdout.truncate(0)

        # Invalid unicode payload
        ret = client.topics['procrun'].request(client.client, invalid_bytes,
                                               timeout=10, procid='1')
        self.assertEqual(ret.decode('utf-8'), 'Error decoding utf-8 payload')

        # Invalid json
        payload = '{"a":'.encode('utf-8')
        ret = client.topics['procrun'].request(client.client, payload,
                                               timeout=10, procid='1')
        self.assertEqual(ret.decode('utf-8'),
                         'Invalid command, should be a json encoded list')

        # Invalid json value
        payload = '3'.encode('utf-8')
        ret = client.topics['procrun'].request(client.client, payload,
                                               timeout=10, procid='1')
        self.assertEqual(ret.decode('utf-8'),
                         'Invalid command')

        client.onecmd('poll 1')
        self.assertEqual(stdout.getvalue(), 'Error process never run\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('rerun 1')
        self.assertEqual(stdout.getvalue(), 'Error process never run\n')
        stdout.seek(0)
        stdout.truncate(0)

        client.onecmd('run 1 invalid_command/no_path')
        # Python3 adds file path
        err = '[Errno 2] No such file or directory'
        self.assertTrue(stdout.getvalue().startswith(err))
        stdout.seek(0)
        stdout.truncate(0)


@mock.patch('sys.stdout', new_callable=StringIO)
class ProcessClientErrorTests(TestCaseImproved):
    """Test ProcessClient Parsing errors."""
    def setUp(self):
        args = ['localhost', '--broker-port', '%s' % 54321,
                '--prefix', 'process/test/prefix',
                '--site', process.MQTTProcessAgent.HOSTNAME]
        opts = process_client.PARSER.parse_args(args)
        self.client = process_client.ProcessShell.from_opts_dict(**vars(opts))
        # Publish should crash
        self.client.publish = None

    def test_new(self, stdout):
        """Test new parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: new [NAME]\n'
               '  NAME: optional process identifier\n')

        # Too many arguments
        self.client.onecmd('new name additional')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_free(self, stdout):
        """Test free parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: free NAME\n'
               '  NAME: process identifier\n')

        # Not enough arguments
        self.client.onecmd('free')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('free name additional')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_list(self, stdout):
        """Test list help."""
        hlp = 'list\n'

        # cannot be done from command, just call it
        self.client.onecmd('help list')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_run(self, stdout):
        """Test run parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: run NAME CMD0 [CMD1 [...]]\n'
               '  NAME: process identifier\n'
               '  CMD: command arguments\n')

        # Not enough arguments
        self.client.onecmd('run')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        self.client.onecmd('run procid1')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_poll(self, stdout):
        """Test poll parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: poll NAME\n'
               '  NAME: process identifier\n')

        # Not enough arguments
        self.client.onecmd('poll')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('poll name additional')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_kill(self, stdout):
        """Test kill parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: kill NAME\n'
               '  NAME: process identifier\n')

        # Not enough arguments
        self.client.onecmd('kill')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('kill name additional')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_rerun(self, stdout):
        """Test rerun parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: rerun NAME\n'
               '  NAME: process identifier\n')

        # Not enough arguments
        self.client.onecmd('rerun')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        # Too many arguments
        self.client.onecmd('rerun name additional')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_stdinline(self, stdout):
        """Test stdinline parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: stdinline NAME message with spaces\n'
               '  NAME: process identifier\n'
               '  Message is sent as utf-8 data with a \\n character\n')

        # Not enough arguments
        self.client.onecmd('stdinline')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        self.client.onecmd('stdinline name')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

    def test_stdinraw(self, stdout):
        """Test stdinraw parser errors."""
        hlp = ('Error: Invalid arguments\n'
               'Usage: stdinraw NAME message with spaces\n'
               '  NAME: process identifier\n'
               '  Message is sent as utf-8 data\n')

        # Not enough arguments
        self.client.onecmd('stdinraw')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)

        self.client.onecmd('stdinraw name')
        self.assertEqual(stdout.getvalue(), hlp)
        stdout.seek(0)
        stdout.truncate(0)
