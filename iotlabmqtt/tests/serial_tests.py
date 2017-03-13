# -*- coding:utf-8 -*-

"""Serial agent tests."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622


import mock

from iotlabmqtt import serial
from . import TestCaseImproved


class LineHandlerTest(TestCaseImproved):
    """Test LineHandler."""
    def test_line_handler_utf_8(self):
        """Test LineHandler newline in utf-8 sequences."""
        unicode_str = 'abĊde\nfgԊȊjk\nmno'
        lines = unicode_str.splitlines(False)

        self.assertEqual(lines, ['ab\u010Ade', 'fg\u050A\u020Ajk', 'mno'])

        callback = mock.Mock()
        line_handler = serial.LineHandler(callback)

        utf8_str = unicode_str.encode('utf-8')
        # Iter on each bytes
        for single_byte in self._bytes_iter(utf8_str):
            line_handler(single_byte)

        # last line incomplete
        calls = [mock.call(line.encode('utf-8')) for line in lines[:-1]]
        callback.assert_has_calls(calls)
        callback.assert_has_calls([])

    @staticmethod
    def _bytes_iter(bytes_str):
        """Python2 / python3 compatible bytes iterator.

        Python2 iter with bytes, python3 with ints.
        http://stackoverflow.com/a/14267935/395687
        """
        return [bytes_str[i:i + 1] for i in range(len(bytes_str))]
