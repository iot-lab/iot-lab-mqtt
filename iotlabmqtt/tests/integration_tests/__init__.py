# -*- coding:utf-8 -*-
"""Tests for IoT-LAB MQTT agents using a real server."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import time
import subprocess
import unittest
import tempfile

from .. import TestCaseImproved


class IntegrationTestCase(TestCaseImproved):
    """Integration tests which run mosquitto."""
    BROKERPORT = 54321

    @classmethod
    def setUpClass(cls):
        cls.mosquitto_conf = cls._mosquitto_conf()
        cls.mqttuser = 'iotlabmqtt'
        cls.mqttpassword = 'mqttpassword'
        cls.proc = cls.mosquitto_start(port=cls.BROKERPORT)

    @classmethod
    def _mosquitto_conf(cls):
        """Generate temporary configuration for mosquitto.

        A generated configuration as I do not know if the path to
        mosquitto.passwd can be relative.
        """
        conf = tempfile.NamedTemporaryFile(suffix='mosquitto_conf')

        template = cls.file_path('mosquitto.conf')
        password_file = cls.file_path('mosquitto.passwd')
        with open(template, 'rb') as tpl:
            config = tpl.read().decode('utf-8')
            config = config.format(password_file=password_file)

        conf.write(config.encode('utf-8'))
        conf.flush()
        return conf

    @classmethod
    def mosquitto_conf_path(cls):
        """Path to mosquitto config file."""
        return cls.mosquitto_conf.name

    @classmethod
    def mosquitto_start(cls, port, wait=5):
        """Start mosquitto on ``port``.

        :param port: mosquitto listening port
        :param wait: waiting time after starting process to check if running
        """
        mosquitto_conf = cls.mosquitto_conf.name
        cmd = ['mosquitto', '-p', '%s' % port, '-c', mosquitto_conf]
        try:
            proc = subprocess.Popen(cmd)

            time.sleep(wait)
            if proc.poll() is None:
                return proc
        except OSError:
            pass

        raise unittest.SkipTest('Could not start "mosquitto"')

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait()
        cls.mosquitto_conf.close()

    def setUp(self):
        self.socat = {}

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

    @staticmethod
    def file_path(name):
        """Return testfile ``name`` path.

        Testfiles are in ``files`` directory.
        """
        return os.path.join(os.path.dirname(__file__), 'files', name)
