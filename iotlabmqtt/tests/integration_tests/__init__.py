# -*- coding:utf-8 -*-
"""Tests for IoT-LAB MQTT agents using a real server."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import sys
import time
import subprocess
import unittest

from .. import TestCaseImproved


class IntegrationTestCase(TestCaseImproved):
    """Integration tests which run mosquitto."""
    BROKERPORT = 54321

    @classmethod
    def setUpClass(cls):
        cls.proc = cls.mosquitto_start(port=cls.BROKERPORT)

    @staticmethod
    def mosquitto_start(port, wait=5):
        """Start mosquitto on ``port``.

        :param port: mosquitto listening port
        :param wait: waiting time after starting process to check if running
        """
        mosquitto_conf = os.path.join(os.path.dirname(__file__),
                                      'mosquitto.conf')
        cmd = ['mosquitto', '-p', '%s' % port, '-c', mosquitto_conf]
        proc = subprocess.Popen(cmd)

        time.sleep(wait)
        if proc.poll() is not None:
            raise unittest.SkipTest('Could not start "mosquitto"')

        return proc

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
