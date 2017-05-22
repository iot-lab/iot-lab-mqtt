# -*- coding:utf-8 -*-

"""MQTTCommon module tests."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os.path
import threading

import mock
from iotlabmqtt import mqttcommon
from iotlabmqtt.clients import common as clientcommon
from . import mqttclient_mock
from . import TestCaseImproved


def wrap_mock(func):
    """Call 'func' mock.

    Should be a real function for 'functools.wraps' callback
    (issues while setting '__name__' in a python2/python3 compatible way).
    """
    def _cb_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return _cb_wrapper


class AgentTest(TestCaseImproved):
    """Setup and cleanup Agent mock."""

    def setUp(self):
        mqttclient_mock.MQTTClientMock.mock_reset()

    def tearDown(self):
        mqttclient_mock.MQTTClientMock.mock_reset()


class MQTTClientTest(AgentTest):
    """Test MQTTClient using wrapper mock."""
    def test_mqttagent_start_stop(self):
        """Test agent start/stop and topics registering."""
        callback = mock.Mock()
        topics = {'one': mqttcommon.Topic('a/b/c', wrap_mock(callback)),
                  'two': mqttcommon.Topic('1/2/3'),
                  # No subscribe for topic 'three'
                  'three': mqttcommon.NullTopic('not_subscribe')}

        agent = mqttclient_mock.MQTTClientMock('localhost', 1883,
                                               list(topics.values()))
        with mock.patch('iotlabmqtt.mqttcommon.print') as stdout:
            agent.start()

        self.assertEqual(agent.topics, list(topics.values()))
        self.assertEqual(agent.on_message_filtered,
                         [('a/b/c', topics['one'].callback)])

        # Not subscribed to 'three' as 'subscribe_topic' is None
        stdout.assert_has_calls([mock.call('Subscribing to: a/b/c'),
                                 mock.call('Subscribing to: 1/2/3')],
                                any_order=True)

        agent.stop()

    def test_mqttagent_start_timeout(self):
        """Test starting agent timeout."""
        agent = mqttclient_mock.MQTTClientMock('localhost', 1883)
        agent.connect_delay = 15
        self.assertRaises(RuntimeError, agent.start)


class TopicTest(AgentTest):
    """Test Topic class."""

    def test_topic(self):
        """Test valid a topic functions."""
        topicname = 'a/b/{val}/{another}'
        callback = mock.Mock()

        topic = mqttcommon.Topic(topicname, callback=wrap_mock(callback))

        self.assertEqual(topic.topic, 'a/b/{val}/{another}')
        self.assertEqual(topic.fields, ['val', 'another'])
        self.assertEqual(topic.subscribe_topic, 'a/b/+/+')
        self.assertEqual(topic.match_re.pattern,
                         'a/b/(?P<val>[^/]+)/(?P<another>[^/]+)')

        values = topic.fields_values('a/b/first/second')
        self.assertEqual(values, {'val': 'first', 'another': 'second'})

    def test_topic_callback(self):
        """Test calling topic callback."""
        topicname = 'a/b/{val}/{another}'

        callback = mock.Mock()
        topic = mqttcommon.Topic(topicname, callback=wrap_mock(callback))

        mqttc = mock.Mock()
        obj = mock.Mock()

        msg_topic = 'a/b/value/argument'
        msg_topic = mqttclient_mock.encode_topic_if_needed(msg_topic)
        msg = mqttcommon.mqtt.MQTTMessage(topic=msg_topic)

        topic.callback(mqttc, obj, msg)

        self.assertTrue(callback.called)
        callback.assert_called_with(msg, val='value', another='argument')

    def test_topic_none_calback(self):
        """Test callback None even after wrapping."""
        callback = None
        topic = mqttcommon.Topic('to/ic', callback=callback)
        self.assertIsNone(topic.callback)


class RequestTest(AgentTest):
    """Test Request classes."""

    def test_request_topic(self):
        """Test RequestTopic."""
        clientid = clientcommon.clientid('testrequest')

        topicname = '{archi}/{num}/line'
        requesttopic = '{archi}/{num}/line/ctl/start/request/%s/{requestid}'
        requesttopic %= clientid
        replytopic = '{archi}/{num}/line/ctl/start/reply/%s/{requestid}'
        replytopic %= clientid

        # Verify topics values
        self.assertEqual(
            mqttcommon.RequestTopic.request_topic(topicname, 'start',
                                                  clientid=clientid),
            requesttopic)
        self.assertEqual(
            mqttcommon.RequestTopic.reply_topic(topicname, 'start',
                                                clientid=clientid),
            replytopic)

        # Request/reply conversion
        self.assertEqual(mqttcommon.RequestTopic.reply_topic_from_request(
            requesttopic), replytopic)
        self.assertEqual(mqttcommon.RequestTopic.request_topic_from_reply(
            replytopic), requesttopic)

        # Check fields values cleanup
        fields_values = {'archi': 'm3', 'num': '1',
                         'clientid': 'CLIENTID', 'requestid': 'REQUESTID'}
        self.assertEqual(
            mqttcommon.RequestTopic.clean_callback_fields(fields_values),
            {'archi': 'm3', 'num': '1'})

    def test_request_topics(self):
        """Test Request Topics."""
        clientid = clientcommon.clientid('testrequest')
        topicname = '{archi}/{num}/line'

        server_cb = mock.Mock()

        client_topics = {'linestart': mqttcommon.RequestClient(
            topicname, 'start', clientid=clientid)}
        server_topics = {'linestart': mqttcommon.RequestServer(
            topicname, 'start', wrap_mock(server_cb))}

        client = mqttclient_mock.MQTTClientMock('localhost', 1883,
                                                list(client_topics.values()))
        server = mqttclient_mock.MQTTClientMock('localhost', 1883,
                                                list(server_topics.values()))

        # Simple request answering
        req_topic = mqttcommon.common.topic_lazyformat(
            server_topics['linestart'].topic,
            archi='m3', num='1', clientid=clientid)

        server_cb.return_value = b'result'
        request_msg = mqttclient_mock.mqttmessage(
            req_topic.format(requestid=1), b'queryone')
        ret = client_topics['linestart'].request(client, b'queryone',
                                                 archi='m3', num='1')
        server_cb.assert_called_with(request_msg, archi='m3', num='1')
        server_cb.reset_mock()
        self.assertEqual(ret, b'result')

        # Async answer
        def _server_cb(msg, archi, num):
            thr = threading.Thread(target=__server__cb,
                                   args=(msg.reply_publisher, b'responsetwo'))
            thr.start()
            return None

        def __server__cb(publisher, payload):
            import time
            time.sleep(1)
            publisher(payload)

        server_cb.side_effect = _server_cb
        request_msg = mqttclient_mock.mqttmessage(
            req_topic.format(requestid=2), b'querytwo')
        ret = client_topics['linestart'].request(client, b'querytwo',
                                                 timeout=5,
                                                 archi='m3', num='1')
        server_cb.assert_called_with(request_msg, archi='m3', num='1')
        server_cb.reset_mock()
        server_cb.side_effect = None
        self.assertEqual(ret, b'responsetwo')

        # Timeout from the server
        server_cb.return_value = None  # ignore return value here
        request_msg = mqttclient_mock.mqttmessage(
            req_topic.format(requestid=3), b'querythree')

        self.assertRaises(RuntimeError,
                          client_topics['linestart'].request,
                          client, b'querythree', timeout=5,
                          archi='m3', num='1')
        server_cb.assert_called_with(request_msg, archi='m3', num='1')
        server_cb.reset_mock()

        # Publish timeout
        server_cb.return_value = b''
        client.publish_delay = 5
        server.publish_delay = 0
        request_msg = mqttclient_mock.mqttmessage(
            req_topic.format(requestid=4), b'queryfour')
        self.assertRaises(RuntimeError,
                          client_topics['linestart'].request,
                          client, b'queryfour', timeout=0.1,
                          archi='m3', num='1')
        self.assertFalse(server_cb.called)

        # Cleanup
        # Wait until callback called
        self.assertEqualTimeout(lambda: server_cb.called, True, timeout=10)


class InputOutputTest(AgentTest):
    """Test InputOutput classes."""

    def test_input_topics(self):
        """Test Input Topics."""
        topicname = '{procid}/fd/stdin'

        server_cb = mock.Mock()
        client_topics = {'in': mqttcommon.InputClient(topicname)}
        server_topics = {'in': mqttcommon.InputServer(topicname,
                                                      wrap_mock(server_cb))}

        client = mqttclient_mock.MQTTClientMock('localhost', 1883,
                                                list(client_topics.values()))
        mqttclient_mock.MQTTClientMock('localhost', 1883,
                                       list(server_topics.values()))

        # Client writes a message
        client_topics['in'].send(client, b'input',
                                 procid='1').wait_for_publish()
        self.assertTrue(server_cb.called)

        write_topic = server_topics['in'].topic.format(procid='1')
        write_msg = mqttclient_mock.mqttmessage(write_topic, b'input')
        server_cb.assert_called_with(write_msg, procid='1')

    def test_output_topics(self):
        """Test Output Topics."""
        topicname = '{procid}/fd/stdout'

        client_cb = mock.Mock()
        client_topics = {'out': mqttcommon.OutputClient(topicname,
                                                        wrap_mock(client_cb))}
        server_topics = {'out': mqttcommon.OutputServer(topicname)}

        client = mqttclient_mock.MQTTClientMock('localhost', 1883,
                                                list(client_topics.values()))
        mqttclient_mock.MQTTClientMock('localhost', 1883,
                                       list(server_topics.values()))

        # Server writes a message
        server_topics['out'].send(client, b'output',
                                  procid='1').wait_for_publish()
        self.assertTrue(client_cb.called)

        read_topic = client_topics['out'].topic.format(procid='1')
        read_msg = mqttclient_mock.mqttmessage(read_topic, b'output')
        client_cb.assert_called_with(read_msg, procid='1')


class ChannelTest(AgentTest):
    """Test Channel classes."""

    def test_channel_topic(self):
        """Test ChannelTopic."""
        topicname = '{archi}/{num}/line'
        output_topic = '{archi}/{num}/line/data/out'
        input_topic = '{archi}/{num}/line/data/in'

        # Verify topics values
        self.assertEqual(mqttcommon.ChannelTopic.output_topic(topicname),
                         output_topic)
        self.assertEqual(mqttcommon.ChannelTopic.input_topic(topicname),
                         input_topic)

        # Output/input conversion
        self.assertEqual(
            mqttcommon.ChannelTopic.output_topic_from_input(input_topic),
            output_topic)
        self.assertEqual(
            mqttcommon.ChannelTopic.input_topic_from_output(output_topic),
            input_topic)

        # Conversion is stable
        self.assertEqual(
            input_topic,
            mqttcommon.ChannelTopic.input_topic_from_output(
                mqttcommon.ChannelTopic.output_topic_from_input(input_topic)))
        self.assertEqual(
            output_topic,
            mqttcommon.ChannelTopic.output_topic_from_input(
                mqttcommon.ChannelTopic.input_topic_from_output(output_topic)))

    def test_channel_topics(self):
        """Test Channel Topics."""
        topicname = '{archi}/{num}/line'

        client_cb = mock.Mock()
        server_cb = mock.Mock()
        client_topics = {'line': mqttcommon.ChannelClient(
            topicname, wrap_mock(client_cb))}
        server_topics = {'line': mqttcommon.ChannelServer(
            topicname, wrap_mock(server_cb))}

        client = mqttclient_mock.MQTTClientMock('localhost', 1883,
                                                list(client_topics.values()))
        server = mqttclient_mock.MQTTClientMock('localhost', 1883,
                                                list(server_topics.values()))

        # Client writes a message
        client_topics['line'].send(client, b'req',
                                   archi='m3', num=1).wait_for_publish()
        self.assertTrue(server_cb.called)

        write_topic = server_topics['line'].topic.format(archi='m3', num='1')
        write_msg = mqttclient_mock.mqttmessage(write_topic, b'req')
        server_cb.assert_called_with(write_msg, archi='m3', num='1')

        # Server writes a message
        line_write = server_topics['line'].output_publisher(
            server, archi='m3', num='1')
        line_write(b'response').wait_for_publish()
        self.assertTrue(client_cb.called)

        read_topic = client_topics['line'].topic.format(archi='m3', num='1')
        read_msg = mqttclient_mock.mqttmessage(read_topic, b'response')
        client_cb.assert_called_with(read_msg, archi='m3', num='1')


class ErrorTest(AgentTest):
    """Test Error classes."""

    def test_error_topic(self):
        """Test ErrorTopic."""
        topic = 'iot-lab/serial/grenoble'
        error_topic = 'iot-lab/serial/grenoble/error/'
        subscribe_topic = 'iot-lab/serial/grenoble/error/#'

        relative_topic_none = ''
        relative_topic_example = 'm3/1/line/data/in'

        # Verify topics values
        self.assertEqual(mqttcommon.ErrorTopic.error_topic(topic), error_topic)
        self.assertEqual(mqttcommon.ErrorTopic.subscribe_topic(topic),
                         subscribe_topic)

        # Test relative topic stability
        self.assertEqual(
            relative_topic_none,
            mqttcommon.ErrorTopic.relative_topic(
                topic, os.path.join(topic, relative_topic_none)))

        self.assertEqual(
            relative_topic_example,
            mqttcommon.ErrorTopic.relative_topic(
                topic, os.path.join(topic, relative_topic_example)))

        self.assertRaises(ValueError, mqttcommon.ErrorTopic.relative_topic,
                          topic, 'topic/not/starting/with/topic')

    def test_error_topics(self):
        """Test Error Topics."""
        topicname = 'iot-lab/serial/grenoble'
        error_topic = 'iot-lab/serial/grenoble/error/'

        client_cb = mock.Mock()
        client_topics = {'error': mqttcommon.ErrorClient(
            topicname, wrap_mock(client_cb))}
        server_topics = {'error': mqttcommon.ErrorServer(topicname)}

        mqttclient_mock.MQTTClientMock('localhost', 1883,
                                       list(client_topics.values()))
        server = mqttclient_mock.MQTTClientMock('localhost', 1883,
                                                list(server_topics.values()))
        server.publish_delay = 0

        err = b'error message'
        topic_with_error_rel = 'm3/1/line/data/in'
        topic_with_error = os.path.join(topicname, topic_with_error_rel)
        server_topics['error'].publish_error(server, topic_with_error, err)

        self.assertTrue(client_cb.called)

        err_msg = mqttclient_mock.mqttmessage(
            os.path.join(error_topic, topic_with_error_rel),
            err)
        client_cb.assert_called_with(err_msg, topic_with_error_rel)
