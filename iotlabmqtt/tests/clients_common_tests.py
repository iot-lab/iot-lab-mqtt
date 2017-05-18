# -*- coding:utf-8 -*-

"""MQTTCommon module tests."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

from iotlabmqtt.clients import common as clientcommon
from . import TestCaseImproved


class TestCmdShell(TestCaseImproved):
    """Test CmdShell methods."""

    def test_cmd_split(self):
        """Test cmd_split method."""
        cmd_split = clientcommon.CmdShell.cmd_split

        # One command
        args = cmd_split('command')
        self.assertEqual(args, ['command'])
        args = cmd_split('command   ')
        self.assertEqual(args, ['command'])

        # Simple arguments
        args = cmd_split('command arg1 arg2 arg3')
        self.assertEqual(args, ['command', 'arg1', 'arg2', 'arg3'])
        args = cmd_split('command arg1 arg2 arg3', maxsplit=1)
        self.assertEqual(args, ['command', 'arg1 arg2 arg3'])

        # With more whitespaces
        args = cmd_split('command   arg1    arg2    arg3')
        self.assertEqual(args, ['command', 'arg1', 'arg2', 'arg3'])
        args = cmd_split('command   arg1    arg2    arg3', maxsplit=1)
        self.assertEqual(args, ['command', 'arg1    arg2    arg3'])
        args = cmd_split('command   arg1    arg2    arg3', maxsplit=2)
        self.assertEqual(args, ['command', 'arg1', 'arg2    arg3'])

        # Empty commands
        args = cmd_split('')
        self.assertEqual(args, [])
        args = cmd_split('   ')
        self.assertEqual(args, [])
