#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""IoT-LAB MQTT Process client example
===================================

This example shows a process client. It runs two processes:

 * one that does echo stdin
 * one that print messages for 5 seconds

And then interracts with them.

.. note::

   This file is just an example that uses bare client library with arbitrary
   design choices and should not be taken as a good implementation reference.

Design choices
--------------

To simplify, only one subscribtion is done for each output topics.
And then, the ``procid`` part is handled by the generic callback.

The communication between the asynchronous callbacks and the main process is
done by using per process/topic Queues.

Running
-------

Example to run with a server with custom agenttopic:

::

   iotlab-mqtt-process --prefix PREFIX --agenttopic AGENTTOPIC BROKER

Then run the client with:

::

   python process_client.py --prefix PREFIX --agenttopic AGENTTOPIC BROKER


To see how topics are used, you can use the log client:

::

   iotlab-mqtt-clients log --prefix PREFIX BROKER

"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import sys
import time
import json
import threading
import logging

import iotlabmqtt.process
from iotlabmqtt import common
from iotlabmqtt import mqttcommon
from iotlabmqtt.clients import common as clientcommon
from iotlabmqtt.processcommon import queue  # Python2/3 handled

# Add logging
logging.basicConfig(level=logging.DEBUG)

PARSER = common.MQTTAgentArgumentParser()
PARSER.add_argument('--agenttopic', help='Agent topic', required=True)

PROCESS_SERVER = iotlabmqtt.process.MQTTProcessAgent


class CustomProcessClient(object):
    """CustomProcessClient that runs two process and interracts with them.

    Asynchronous messages are stored in queues.
    Queues can be accessed with ``process_queue(procid, name)`` method.
    Where name is in ('stdout', 'stderr', 'retcode').
    """

    QUEUES = ('stdout', 'stderr', 'retcode')

    def __init__(self, client, prefix, agenttopic):
        _topics = mqttcommon.generate_topics_dict(PROCESS_SERVER.TOPICS,
                                                  prefix, agenttopic)

        clientid = clientcommon.clientid('customprocessclient')
        # Copied from clients/process.py
        self.topics = {
            'new': mqttcommon.RequestClient(
                _topics['agenttopic'], 'new', clientid=clientid),
            'list': mqttcommon.RequestClient(
                _topics['agenttopic'], 'list', clientid=clientid),
            'free': mqttcommon.RequestClient(
                _topics['agenttopic'], 'free', clientid=clientid),
            'freeall': mqttcommon.RequestClient(
                _topics['agenttopic'], 'freeall', clientid=clientid),

            # I use common callback for all processes
            'procrun': mqttcommon.RequestClient(
                _topics['process'], 'run', clientid=clientid),
            'procpoll': mqttcommon.RequestClient(
                _topics['process'], 'poll', clientid=clientid),
            'prockill': mqttcommon.RequestClient(
                _topics['process'], 'kill', clientid=clientid),
            'procrerun': mqttcommon.RequestClient(
                _topics['process'], 'rerun', clientid=clientid),

            'procstdin': mqttcommon.InputClient(_topics['procstdin']),
            'procstdout': mqttcommon.OutputClient(_topics['procstdout'],
                                                  callback=self._stdout_cb),
            'procstderr': mqttcommon.OutputClient(_topics['procstderr'],
                                                  callback=self._stderr_cb),

            'procret': mqttcommon.OutputClient(_topics['procret'],
                                               callback=self._returncode_cb),

            'error': mqttcommon.ErrorClient(_topics['agenttopic'],
                                            callback=self.error_cb),
        }
        self._rlock = threading.RLock()
        self._process_queues = {}

        self.client = client
        self.client.topics = list(self.topics.values())

    def error_cb(self, message, relative_topic):  # pylint:disable=no-self-use
        """Callback on 'error' topic."""
        msg = message.payload.decode('utf-8')
        print('PROCESS ERROR: %s: %s' % (relative_topic, msg), file=sys.stderr)

    def process_queue(self, procid, name):
        """Return given `procid` `name` process_queue.

        Create the Queue object if it does not currently exist.
        """
        assert name in self.QUEUES

        with self._rlock:
            proc_queues = self._process_queues.setdefault(procid, {})
            return proc_queues.setdefault(name, queue.Queue())

    def _save_payload(self, name, message, procid):
        """Store payload in 'self._process_queues[procid][name]' Queue."""
        logging.debug('_save_payload(%s, %s): %r', procid, name,
                      message.payload)
        proc_q = self.process_queue(procid, name)
        proc_q.put(message.payload)

    def _stdout_cb(self, message, procid):
        self._save_payload('stdout', message, procid)

    def _stderr_cb(self, message, procid):
        self._save_payload('stderr', message, procid)

    def _returncode_cb(self, message, procid):
        self._save_payload('retcode', message, procid)

    def start(self):
        """Start Agent."""
        self.client.start()

    def stop(self):
        """Stop agent."""
        self.client.stop()


ECHO_COMMAND = ['cat']
LONG_COMMAND = ['bash', '-c', "for i in {1..5}; do echo $i; sleep 1; done"]


def main(proc_client):
    try:
        process_client.start()
        _main(process_client)
    finally:
        process_client.stop()


def _main(proc_client):  # noqa
    """Execute two processes and use their output.

    One first that echoes data, the other one that execute, returns
    an output and exit.

    :param proc_client: a started CustomProcessClient
    """
    # proc_client is already started

    echo_proc_name = 'echo'
    logging.info('Get a new process with name %s', echo_proc_name)
    ret = proc_client.topics['new'].request(
        proc_client.client, echo_proc_name.encode('utf-8'), timeout=5)
    ret_name = ret.decode('utf-8')
    assert echo_proc_name == ret_name, \
        'Proc new failed %s != %s' % (echo_proc_name, ret_name)
    logging.info('Success')

    logging.info('Get a new process without name')
    ret = proc_client.topics['new'].request(proc_client.client, b'', timeout=5)
    long_proc_name = ret.decode('utf-8')
    assert long_proc_name.isdigit(), 'Proc new failed %s' % long_proc_name
    logging.info('Success, name == %s', long_proc_name)

    logging.info('Start echo process: %s', ECHO_COMMAND)
    ret = proc_client.topics['procrun'].request(
        proc_client.client, json.dumps(ECHO_COMMAND).encode('utf-8'),
        procid=echo_proc_name, timeout=5)
    assert not ret

    ret = proc_client.topics['list'].request(proc_client.client, b'',
                                             timeout=5)
    logging.info('List of processes: %s', json.loads(ret.decode('utf-8')))

    logging.info('Start long process: %s', LONG_COMMAND)
    ret = proc_client.topics['procrun'].request(
        proc_client.client, json.dumps(LONG_COMMAND).encode('utf-8'),
        procid=long_proc_name, timeout=5)
    assert not ret

    # Interracting with long process
    logging.info('Wait long process stops')
    retcodequeue = process_client.process_queue(long_proc_name, 'retcode')
    stdoutqueue = process_client.process_queue(long_proc_name, 'stdout')

    ret = retcodequeue.get(True, 10)
    logging.info('Long process ret: %s', ret.decode('utf-8'))

    output = b''
    for i in range(0, 100):
        try:
            output += stdoutqueue.get_nowait()
            logging.debug('Get stdout Loop %s', i)
        except queue.Empty:
            break
    else:
        logging.info('Should have been out of loop before...')
    logging.info('Long process decoded output: %r', output.decode('utf-8'))

    # Interracting with echo process
    retcodequeue = process_client.process_queue(echo_proc_name, 'retcode')
    stdoutqueue = process_client.process_queue(echo_proc_name, 'stdout')
    for i in range(0, 3):
        logging.info('Sending message %s to echo stdin', i)
        message = ('Echo this: %s\n' % i).encode('utf-8')
        proc_client.topics['procstdin'].send(proc_client.client,
                                             message, procid=echo_proc_name)
        time.sleep(1)

    output = b''
    for i in range(0, 100):
        try:
            output += stdoutqueue.get_nowait()
            logging.debug('Get stdout Loop %s', i)
        except queue.Empty:
            break
    else:
        logging.info('Should have been out of loop before...')
    logging.info('Echo process decoded output: %r', output.decode('utf-8'))

    logging.info('Kill echo process')
    ret = proc_client.topics['prockill'].request(
        proc_client.client, b'', procid=echo_proc_name, timeout=5)
    assert not ret

    logging.info('Wait returncode')
    ret = retcodequeue.get(True, 10)
    logging.info('Echo process ret (killed): %s', ret.decode('utf-8'))

    logging.info('Free %s', long_proc_name)
    ret = proc_client.topics['free'].request(
        proc_client.client, long_proc_name.encode('utf-8'), timeout=5)
    assert not ret

    logging.info('Free %s', echo_proc_name)
    ret = proc_client.topics['free'].request(
        proc_client.client, echo_proc_name.encode('utf-8'), timeout=5)
    assert not ret

    ret = proc_client.topics['list'].request(proc_client.client, b'',
                                             timeout=5)
    logging.info('List of processes: %s', json.loads(ret.decode('utf-8')))


if __name__ == '__main__':
    opts = PARSER.parse_args()
    client = mqttcommon.MQTTClient.from_opts_dict(**vars(opts))
    process_client = CustomProcessClient(client, prefix=opts.prefix,
                                         agenttopic=opts.agenttopic)
    main(process_client)
