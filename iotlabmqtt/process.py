# -*- coding: utf-8 -*-

r"""IoT-LAB MQTT process agent
=============================

Process agent allows running and managing processes.

Process agent base topic: ::

   {prefix}/iot-lab/process/{site}

Every topics from process agent topics start by this topic prefix

:param prefix: configured prefix
:param site: site where the agent is run

.. note::

   ``iot-lab/process/{site}`` part can be replaced with the ``--agenttopic``
   option to allow running it on other servers than IoT-LAB.

Topics Summary
==============

.. |proc|             replace::  ``{processagenttopic}``

.. |ctlnew|           replace::  |proc|\ ``/ctl/new``
.. |ctllist|          replace::  |proc|\ ``/ctl/list``
.. |ctlfree|          replace::  |proc|\ ``/ctl/free``

.. |procid|           replace::  |proc|\ ``/process/{procid}``
.. |procctlrun|       replace::  |procid|\ ``/ctl/run``
.. |procctlpoll|      replace::  |procid|\ ``/ctl/poll``
.. |procctlkill|      replace::  |procid|\ ``/ctl/kill``
.. |procctlrerun|     replace::  |procid|\ ``/ctl/rerun``

.. |fdin|             replace::  ``fd/stdin``
.. |fdout|            replace::  ``fd/stdout``
.. |fderr|            replace::  ``fd/stderr``
.. |procstdin|        replace::  |procid|\ /\ |fdin|
.. |procstdout|       replace::  |procid|\ /\ |fdout|
.. |procstderr|       replace::  |procid|\ /\ |fderr|

.. |retcode|          replace::  ``event/returncode``
.. |procret|          replace::  |procid|\ /\ |retcode|

.. |error_t|          replace::  |proc|\ ``/error/``
.. |request|          replace::  :ref:`Request <RequestTopic>`
.. |error|            replace::  :ref:`Error <ErrorTopic>`

.. |request_topic|    replace::  *{topic}*/**request/{clientid}/{requestid}**
.. |reply_topic|      replace::  *{topic}*/**reply/{clientid}/{requestid}**

.. |outtopic|         replace::  Output
.. |intopic|          replace::  Input

+-+---------------------------------------------------------------+-----------+
| |Topic                                                          | Type      |
+=+===============================================================+===========+
|  **Process agent**                                                          |
+-+---------------------------------------------------------------+-----------+
| ``{prefix}/iot-lab/process/{site}``                                         |
+-+---------------------------------------------------------------+-----------+
| ||error_t|                                                      | |error|   |
+-+---------------------------------------------------------------+-----------+
|  **Process ids management**                                                 |
+-+---------------------------------------------------------------+-----------+
| ||ctlnew|                                                       ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||ctlfree|                                                      ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||ctllist|                                                      ||request|  |
+-+---------------------------------------------------------------+-----------+
|  **Process control**                                                        |
+-+---------------------------------------------------------------+-----------+
| ||procctlrun|                                                   ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||procctlpoll|                                                  ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||procctlkill|                                                  ||request|  |
+-+---------------------------------------------------------------+-----------+
| ||procctlrerun|                                                 ||request|  |
+-+---------------------------------------------------------------+-----------+
|  **Process file descriptors**                                               |
+-+---------------------------------------------------------------+-----------+
| ||procstdin|                                                    | |intopic| |
+-+---------------------------------------------------------------+-----------+
| ||procstdout|                                                   | |outtopic||
+-+---------------------------------------------------------------+-----------+
| ||procstderr|                                                   | |outtopic||
+-+---------------------------------------------------------------+-----------+
|  **Process events**                                                         |
+-+---------------------------------------------------------------+-----------+
| ||procret|                                                      | |outtopic||
+-+---------------------------------------------------------------+-----------+


Process Agent global topics
===========================

Error Topic
-----------

Asynchronous error messages are posted to error topic.
Failure on requests are not duplicated here.

* |error_t|


For format see: :ref:`ErrorTopic`


Process ids management topics
=============================

To run a process, a process id should first be allocated.
This id will be used for every commands on the process.

.. note::

   Seperating this from the ``procrun`` command allows registering first to
   all interesting topics (e.g. ``fd/stdout``, ``event/returncode``) so no
   messages are missed.


New process id
--------------

Allocate a new process id, if a ``procid`` is given it will use this one or
if empty, an uniq integer one will be provided.

Process ids will either be the provided ones, or a string representation of
integers.

:param procid: ``procid`` can be given or empty to get an uniq ``int`` one.
               An error is returned if given one is already used.
               It cannot contain ``{}/+#``.
:type procid:  ``utf-8`` encoded string
:returns:      ``utf-8`` allocated procid, which is either the given one or
               an ``int`` string.
               If message does not match above rules, its an error message.


+-----------------------------------------------------------------------------+
| ``new`` request:                                                            |
+============+================================================================+
| Topic:     |    |ctlnew|                                                    |
+------------+----------------------------------------+-----------------------+
|**Message** | **Topic**                              | **Payload**           |
+------------+----------------------------------------+-----------------------+
| Request    | |request_topic|                        | *empty* or ``procid`` |
+------------+----------------------------------------+-----------------------+
| Reply      | |reply_topic|                          |``procid`` or error_msg|
+------------+----------------------------------------+-----------------------+


Free process id
---------------

Free given process id. Process should be idle.

:param procid: ``utf-8`` ``procid`` to release
:type procid: ``utf-8`` encoded string


+-----------------------------------------------------------------------------+
| ``free`` request:                                                           |
+============+================================================================+
| Topic:     |    |ctlfree|                                                   |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | ``procid``           |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


List processes ids
------------------

List processes ids.

:returns: ``utf-8`` encoded json list of ids

+-----------------------------------------------------------------------------+
| ``list`` request:                                                           |
+============+================================================================+
| Topic:     |    |ctllist|                                                   |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | ``utf-8 json list``  |
+------------+-----------------------------------------+----------------------+


Process control
===============

Control process execution.

Process run
-----------

Run given command for given process id. The process should currently be idle.

:param command: ``utf-8`` encoded json list of arguments

+-----------------------------------------------------------------------------+
| ``run`` request:                                                            |
+============+================================================================+
| Topic:     |    |procctlrun|                                                |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *command*            |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Process poll
------------

Check if given process is still running.
If stopped, it returns returncode else an empty message.

:returns: empty if running, returncode ``int`` string if stopped or
          an error message.

+-----------------------------------------------------------------------------+
| ``poll`` request:                                                           |
+============+================================================================+
| Topic:     |    |procctlpoll|                                               |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or           |
|            |                                         | ``returncode`` or    |
|            |                                         | error_msg            |
+------------+-----------------------------------------+----------------------+


Process kill
------------

Kill given process.

.. note::
   A SIGTERM is first sent, then a SIGKILL one second after if still running.

+-----------------------------------------------------------------------------+
| ``kill`` request:                                                           |
+============+================================================================+
| Topic:     |    |procctlkill|                                               |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Process rerun
-------------

Re-run given process with the same command.
The process should currently be idle.

+-----------------------------------------------------------------------------+
| ``rerun`` request:                                                          |
+============+================================================================+
| Topic:     |    |procctlrerun|                                              |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Process file descriptors
========================

Process standard input, output and error topics.
They transport raw data to allow exchanging everything with the application.

This implies that messages may not be ``utf-8`` data,
or not seperated on new lines characters or even split in the middle of
an ``utf-8`` code-point.

Sent messages are only empty on process termination,
where ``fd/stdout`` and ``fd/stderr`` receive a final empty message.
During normal execution output messages are never empty.


+-----------------------------------------------------------------------------+
| **Process file descriptors**                                                |
+============+================================================================+
| Topic:     |    |procid|                                                    |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Input      | |fdin|                                  | RAW bytes            |
+------------+-----------------------------------------+----------------------+
| Output     | |fdout|                                 | RAW bytes            |
+------------+-----------------------------------------+----------------------+
| Output     | |fderr|                                 | RAW bytes            |
+------------+-----------------------------------------+----------------------+


Process events
==============

Sends process returncode as a ``int`` string on process termination.

+-----------------------------------------------------------------------------+
| **Events  file descriptors**                                                |
+============+================================================================+
| Topic:     |    |procid|                                                    |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Output     | |retcode|                               | ``returncode string``|
+------------+-----------------------------------------+----------------------+
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import json

from . import common
from . import mqttcommon
from . import processcommon

PARSER = common.MQTTAgentArgumentParser()
PARSER.add_agenttopic_argument()


class MQTTProcessAgent(object):
    """Process Manager Agent implementation for MQTT."""
    AGENTTOPIC = 'iot-lab/process/{site}'
    TOPICS = {
        'process': 'process/{procid}',
        'procstdin': 'process/{procid}/fd/stdin',
        'procstdout': 'process/{procid}/fd/stdout',
        'procstderr': 'process/{procid}/fd/stderr',
        'procret': 'process/{procid}/event/returncode',
    }
    HOSTNAME = common.hostname()

    def __init__(self, client, prefix='', agenttopic=None):
        super().__init__()

        staticfmt = {'site': self.HOSTNAME}
        agenttopic = agenttopic if agenttopic is not None else self.AGENTTOPIC
        _topics = mqttcommon.generate_topics_dict(self.TOPICS, prefix,
                                                  agenttopic, staticfmt)

        self.topics = {
            'new': mqttcommon.RequestServer(
                _topics['agenttopic'], 'new', callback=self.cb_new),
            'free': mqttcommon.RequestServer(
                _topics['agenttopic'], 'free', callback=self.cb_free),
            'list': mqttcommon.RequestServer(
                _topics['agenttopic'], 'list', callback=self.cb_list),

            # Used for errors
            'process': mqttcommon.NullTopic(_topics['process']),
            'procrun': mqttcommon.RequestServer(
                _topics['process'], 'run', callback=self.cb_procrun),
            'procpoll': mqttcommon.RequestServer(
                _topics['process'], 'poll', callback=self.cb_procpoll),
            'prockill': mqttcommon.RequestServer(
                _topics['process'], 'kill', callback=self.cb_prockill),
            'procrerun': mqttcommon.RequestServer(
                _topics['process'], 'rerun', callback=self.cb_procrerun),

            'procstdin': mqttcommon.InputServer(_topics['procstdin'],
                                                callback=self.cb_procstdin),
            'procstdout': mqttcommon.OutputServer(_topics['procstdout']),
            'procstderr': mqttcommon.OutputServer(_topics['procstderr']),
            'procret': mqttcommon.OutputServer(_topics['procret']),

            'error': mqttcommon.ErrorServer(_topics['agenttopic']),
        }

        proc_callbacks = (self._closed_cb, self._stdout_cb, self._stderr_cb,
                          self._error_cb)
        self.process = processcommon.ProcessManager(callbacks=proc_callbacks)

        self.client = client
        self.client.topics = list(self.topics.values())

    def error(self, topic, message):
        """Publish error that happend on topic."""
        self.topics['error'].publish_error(self.client, topic,
                                           message.encode('utf-8'))

    def cb_new(self, message):
        """Alloc a new process id.

        If a payload is given, try to use it as processid name.
        Name cannot contain '/{}+#' characters.

        :returns: process id
        """
        try:
            name = message.payload.decode('utf-8')
            self._valid_name(name)
            return self.process.new(name).encode('utf-8')
        except UnicodeError:
            return 'Error decoding utf-8 payload'.encode('utf-8')
        except (KeyError, ValueError) as err:
            return err.args[0].encode('utf-8')

    @staticmethod
    def _valid_name(name=''):
        """Check 'name' is valid == no MQTT special characters."""
        invalid_chars = '/{}+#'
        valid_name = set(invalid_chars).isdisjoint(set(name))
        if not valid_name:
            raise ValueError('Name should not contain %s' % invalid_chars)

    def cb_free(self, message):
        """Free given process id.

        Process should be idle.
        """
        try:
            name = message.payload.decode('utf-8')
            self.process.free(name)
            return ''.encode('utf-8')
        except UnicodeError:
            return 'Error decoding utf-8 payload'.encode('utf-8')
        except KeyError:
            return ('Name %s not found' % name).encode('utf-8')
        except RuntimeError as err:
            return err.args[0].encode('utf-8')

    def cb_list(self, _):
        """List current processes."""
        return json.dumps(self.process.list()).encode('utf-8')

    # Process commands

    def cb_procrun(self, message, procid):
        """Run command for process id.

        Message payload should be the json encoded list of arguments.
        """
        try:
            proc = self.process[procid]
            command = json.loads(message.payload.decode('utf-8'))
            return proc.run(command).encode('utf-8')
        except UnicodeError:
            return 'Error decoding utf-8 payload'.encode('utf-8')
        except (ValueError, TypeError):
            err = 'Invalid command, should be a json encoded list'
            return err.encode('utf-8')
        except KeyError:
            return ('Name %s not found' % procid).encode('utf-8')

    def cb_procpoll(self, _, procid):
        """Check if given process is finished.

        :returns: process returncode if finished.
        """
        try:
            proc = self.process[procid]
            return proc.poll().encode('utf-8')
        except KeyError:
            return ('Name %s not found' % procid).encode('utf-8')

    def cb_prockill(self, _, procid):
        """Kill given process."""
        try:
            proc = self.process[procid]
            return proc.kill().encode('utf-8')
        except KeyError:
            return ('Name %s not found' % procid).encode('utf-8')

    def cb_procrerun(self, _, procid):
        """Rerun given process with the same arguments."""
        try:
            proc = self.process[procid]
            return proc.rerun().encode('utf-8')
        except KeyError:
            return ('Name %s not found' % procid).encode('utf-8')

    def cb_procstdin(self, message, procid):
        """Send message to given process standard input."""
        try:
            proc = self.process[procid]
            proc.write(message.payload)
        except KeyError:
            topic = self.topics['procstdin'].topic.format(procid=procid)
            self.error(topic, 'No process on %s' % procid)

    # Process callbacks

    def _stdout_cb(self, name, data):
        """Process callback for stdout data."""
        self.topics['procstdout'].send(self.client, data, procid=name)

    def _stderr_cb(self, name, data):
        """Process callback for stderr data."""
        self.topics['procstderr'].send(self.client, data, procid=name)

    def _closed_cb(self, name, returncode):
        """Process callback when process closes."""
        data = ('%s' % returncode).encode('utf-8')
        self.topics['procret'].send(self.client, data, procid=name)

    def _error_cb(self, name, message):
        """Process callback when an error occurs."""
        topic = self.topics['process'].topic.format(procid=name)
        self.error(topic, message)

    # Agent running

    def run(self):
        """Run agent."""
        try:
            self.start()
            common.wait_sigint()
        finally:
            self.stop()

    def start(self):
        """Start Agent."""
        self.client.start()
        self.process.start()

    def stop(self):
        """Stop agent."""
        self.process.stop()
        self.client.stop()

    @classmethod
    def from_opts_dict(cls, prefix, agenttopic=None, **kwargs):
        """Create class from argparse entries."""
        client = mqttcommon.MQTTClient.from_opts_dict(**kwargs)
        return cls(client, prefix, agenttopic=agenttopic)


def main():
    """Run process agent."""
    opts = PARSER.parse_args()
    aggr = MQTTProcessAgent.from_opts_dict(**vars(opts))
    aggr.run()
