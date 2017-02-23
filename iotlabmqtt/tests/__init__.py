# -*- coding:utf-8 -*-
"""Tests for IoT-LAB MQTT"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
import unittest


class TestCaseImproved(unittest.TestCase):
    """TestCase class with helper methods."""

    def assertEqualTimeout(self,  # pylint:disable=invalid-name
                           func, ret, timeout, step=0.1):
        """Assert func return equals ret before timeout."""
        end = time.time() + timeout
        while time.time() < end:
            if func() == ret:
                break
            time.sleep(step)
        self.assertEqual(func(), ret)
