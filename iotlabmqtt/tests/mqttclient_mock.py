# -*- coding:utf-8 -*-

"""MQTTCommon module tests."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import time
import threading
import packaging.version
from iotlabmqtt import mqttcommon


class MQTTMessage(mqttcommon.mqtt.MQTTMessage):  # pylint:disable=R0903
    """Add 'eq' to MQTTMessage for Mock use."""

    def __eq__(self, other):
        # Compare internal dicts, except 'info' as not important for tests
        self_d = self._simple_dict(self)
        other_d = self._simple_dict(other)

        ret = self_d == other_d

        if not ret:
            print(self_d)
            print(other_d)

        return ret

    @staticmethod
    def _simple_dict(obj):
        """__dictw_ without values that should not compared."""
        obj_d = obj.__dict__.copy()
        obj_d.pop('info')
        obj_d.pop('reply_publisher', None)
        return obj_d


def encode_topic_if_needed(topic):
    """Encode topic if required for specific paho and python version."""
    import sys  # pylint:disable=redefined-outer-name
    if sys.version_info[0] < 3:
        return topic

    # Handle new MQTTMessage version
    version_needs_bytes = packaging.version.parse('1.2.1')
    if mqttcommon.PAHO_VERSION >= version_needs_bytes:
        return topic.encode('utf-8')

    return topic


def mqttmessage(topic, payload):
    """Create message for topic/payload."""
    topic = encode_topic_if_needed(topic)
    msg = MQTTMessage(topic=topic)
    # Handle '_bytes_safe_payload'
    if isinstance(payload, bytearray):
        payload = bytes(payload)

    msg.payload = payload
    return msg


class MQTTClientMock(mqttcommon.MQTTClient):
    """Mock for MQTTClient."""
    ON_MESSAGE_FILTERED = []
    PUBLISH_DELAY = 1
    SUBSCRIBE_DELAY = 1
    CONNECT_DELAY = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Share all callbacks
        self.on_message_filtered = MQTTClientMock.ON_MESSAGE_FILTERED
        self._register_topics_callbacks()

        self.publish_delay = self.PUBLISH_DELAY
        self.subscribe_delay = self.SUBSCRIBE_DELAY
        self.connect_delay = self.CONNECT_DELAY

    @classmethod
    def mock_reset(cls):
        """Cleanup callbacks."""
        del cls.ON_MESSAGE_FILTERED[:]

    def _send_publish(self,  # pylint:disable=too-many-arguments
                      mid, topic, payload=None,
                      qos=0, retain=False, dup=False, info=None):
        """Mock _send_publish function in 'qos == 0' mode."""
        assert info, 'Only info set managed currently'
        assert qos == 0, 'Only qos === 0 managed in tests.'

        self.async_send_message(mqttmessage(topic, payload), info)
        return info

    def async_send_message(self, message, info):
        """Start a thread thatThread run function to publish message."""
        if self.publish_delay:
            threading.Thread(target=self._async_send_message,
                             args=(message, info)).start()
        else:
            self._async_send_message(message, info)

    def _async_send_message(self, message, info):
        """Thread run function to publish message."""
        time.sleep(self.publish_delay)
        self._handle_on_message(message)
        # Set published after 'handled' to ease tests
        info._set_as_published()  # pylint:disable=protected-access

    def subscribe(self, *args, **kwargs):
        # pylint:disable=unused-argument,arguments-differ
        threading.Thread(target=self._subscribe).start()

    def _subscribe(self):
        time.sleep(self.subscribe_delay)
        self.on_subscribe(self, None, None, 0)  # pylint:disable=not-callable

    def connect(self, *args, **kwargs):
        # pylint:disable=unused-argument,arguments-differ
        threading.Thread(target=self._connect).start()

    def _connect(self):
        time.sleep(self.connect_delay)
        self.on_connect(self, None, 0, 0)  # pylint:disable=not-callable

    def loop_start(self):
        pass

    def loop_stop(self, force=False):  # pylint:disable=unused-argument
        pass
