# -*- coding:utf-8 -*-

"""Common MQTT class for iotlabmqtt agents."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import re
import os.path
import functools
import contextlib
import threading
import packaging.version

import paho.mqtt
import paho.mqtt.client as mqtt

from . import common

PAHO_VERSION = packaging.version.parse(paho.mqtt.__version__)


class MQTTClient(mqtt.Client):
    """MQTT Agent implementation."""

    SUBSCRIBE_TIMEOUT = 10

    def __init__(self, server, port, topics=None):
        super().__init__()

        self.server = server
        self.port = int(port or 1883)
        self.topics = topics or ()

        self._subscribed = threading.Event()

    def on_connect(self, mqttc, obj, flags, rc):  # pylint:disable=W0221,W0613
        """On connect, subscribe to all topics."""
        self._subscribe_topics()

    def _subscribe_topics(self):
        """Suscribe to topics."""
        subtopics = self._subscribable_topics()
        # No subscribe to do
        if not subtopics:
            self._subscribed.set()
            return

        self._log_sub_topic(subtopics)

        topics = (t.subscribe_topic for t in subtopics)
        topics = (self._paho_topic_python2_3(t) for t in topics)
        topics_list = [(t, 0) for t in topics]

        self._subscribed.clear()
        self.subscribe(topics_list)

    @staticmethod
    def _paho_topic_python2_3(topic):
        """Fix issue with paho 1.2.x and python2.

        It requires a 'str' topic and tries to encode it to 'utf-8' after.
        For python2, force it to be ascii bytes so auto-conversion will work.
        """
        import sys  # pylint:disable=redefined-outer-name
        if sys.version_info[0] >= 3:
            return topic

        # Handle paho-mqtt 1.2.x
        if (PAHO_VERSION >= packaging.version.parse('1.2') or
                PAHO_VERSION < packaging.version.parse('1.3')):
            return topic.encode('ascii')

        # It may change in 1.3, so raise a warning to force to check this
        from warnings import warn
        warn('paho-mqtt version %s has not been validated' % PAHO_VERSION)

        return topic

    def _subscribable_topics(self):
        """Topics that are subscrible."""
        return [t for t in self.topics if t.subscribe_topic is not None]

    @staticmethod
    def _log_sub_topic(topics):
        """Log on which subscribed we are subscribing."""
        for topic in topics:
            print('Subscribing to: %s' % (topic.topic,))

    def on_subscribe(self, mqttc, obj, mid, qos):  # pylint:disable=W0221,W0613
        """Unlock '_subscribed' event."""
        self._subscribed.set()

    # def on_publish(self, mqttc, obj, mid):  #  Ignore

    def on_message(self, mqttc, obj, msg):  # pylint:disable=W0221,W0613
        # This should do an error
        print('on_message(%s): %r' % (msg.topic, msg.payload))

    def on_log(self, mqttc, obj, level, string):  # pylint:disable=W0221,W0613
        if level != 16:
            # This should do an error
            print('on_log(%r): %s' % (level, string))

    def start(self):
        """Start MQTT Agent and subscribe to topics."""
        self._register_topics_callbacks()

        self.connect(self.server, self.port)
        self.loop_start()

        subscribed = self._subscribed.wait(self.SUBSCRIBE_TIMEOUT)
        if not subscribed:
            raise RuntimeError('Topics subscribe timeout')

    def _register_topics_callbacks(self):
        """Register the callbacks for topics."""
        topics = (t for t in self.topics if t.callback is not None)
        for topic in topics:
            self.message_callback_add(topic.subscribe_topic, topic.callback)

    def stop(self):
        """Stop MQTT Agent."""
        self.loop_stop()

    @contextlib.contextmanager
    def message_callback(self, topic, callback):
        """Contextmanager that sets topic callback for current context."""
        self.message_callback_add(topic, callback)
        try:
            yield
        finally:
            self.message_callback_remove(topic)

    def publisher(self, topic):
        """Return a function that publishes on ``topic``."""
        return functools.partial(self.publish, topic)

    def publish(self, topic, payload=None, qos=0, retain=False):
        """Publish but requires strings to be bytes."""
        payload = self._bytes_safe_payload(payload)
        return super().publish(topic, payload=payload, qos=qos, retain=retain)

    @staticmethod
    def _bytes_safe_payload(payload):
        """Convert 'payload' to be a bytearray if type 'bytes'.
        Reject 'str' as it allows not managing encoding.

        paho-mqtt (1.2) does not correctly handles python2 'str'
        (== python3 bytes) and tries to encode them to 'utf-8'.
        Giving a ``bytearray`` circumvents it.
        https://github.com/eclipse/paho.mqtt.python/issues/125
        """
        assert not isinstance(payload, str)
        if isinstance(payload, bytes):
            return bytearray(payload)
        return payload

    @classmethod
    def from_opts_dict(cls, broker, broker_port, **_):
        """Create class from argparse entries."""
        return cls(broker, port=broker_port)


def _fmt_topic(topic, prefix='', static_fmt_dict=None):
    """Prepend prefix to prefix and update values from static_fmt_dict.

    >>> _fmt_topic('a/{b}/c/{d}', 'pfx', {'b': 'B'}) == 'pfx/a/B/c/{d}'
    True
    >>> _fmt_topic('a/{b}/c/{d}') == 'a/{b}/c/{d}'
    True
    """
    static_fmt_dict = static_fmt_dict or {}
    topic = os.path.join(prefix, topic)
    topic = common.topic_lazyformat(topic, **static_fmt_dict)
    return topic


def generate_topics_dict(topics_dict, prefix='', agenttopic='',
                         static_fmt_dict=None):
    """Generate full topics dict and add 'agenttopic'."""

    topics = {k: os.path.join(agenttopic, v) for k, v in topics_dict.items()}
    topics['agenttopic'] = agenttopic

    return format_topics_dict(topics, prefix, static_fmt_dict)


def format_topics_dict(topic_dict, prefix='', static_fmt_dict=None):
    """Return a new dict with formatted topics.

    >>> topics = {'a': 'a/{b}/c/{d}', 'b': '1/2/{three}'}
    >>> ret = {'a': 'pfx/a/B/c/{d}', 'b': 'pfx/1/2/3'}

    >>> format_topics_dict(topics, 'pfx', {'b': 'B', 'three': '3'}) == ret
    True
    """

    formatted_topics = {n: _fmt_topic(t, prefix, static_fmt_dict)
                        for n, t in topic_dict.items()}
    return formatted_topics


class Topic(object):
    """Topic base class."""
    LEVEL = r'(?P<%s>[^/]+)'

    def __init__(self, topic, callback=None):
        self.topic = topic
        self.fields = common.topic_fields(self.topic)
        self.subscribe_topic = self._topic_wildcard(self.topic, *self.fields)
        self.match_re = self._topic_match_re(self.topic, *self.fields)
        self.callback = self.wrap_callback(callback) if callback else None

    def fields_values(self, topic):
        """Extract named fields values from actual topic."""
        match = self.match_re.match(topic)
        fields = {f: match.group(f) for f in self.fields}
        return fields

    def wrap_callback(self, callback):
        """Wrap callback to call it with fields arguments values."""
        @functools.wraps(callback)
        def _wrapper(mqttc, obj, msg):  # pylint:disable=unused-argument
            fields = self.fields_values(msg.topic)
            return callback(msg, **fields)

        return _wrapper

    @staticmethod
    def _topic_wildcard(topic, *fields):
        """Convert `topic` named `fields` to '+' mqtt wildcard."""
        fmts = {f: '+' for f in fields}
        return topic.format(**fmts)

    @classmethod
    def _topic_match_re(cls, topic, *fields):
        """Convert `topic` to a re pattern that extracts fields values."""
        fmts = {f: cls.LEVEL % f for f in fields}
        return re.compile(topic.format(**fmts))


class NullTopic(Topic):
    """NullTopic just to store Topic value."""

    def __init__(self, topic, callback=None):
        assert callback is None
        super().__init__(topic, callback)
        # Disable subscription for NullTopic
        self.subscribe_topic = None


class InputServer(Topic):
    """Topic implementation for an Input Server."""
    pass


class InputClient(NullTopic):
    """Topic implementation for an Input Client."""

    def send(self, client, data, **fmt):
        """Send ``data`` to topic formatted with **fmt."""
        topic = self.topic.format(**fmt)
        return client.publish(topic, data)


class OutputServer(InputClient):
    """Topic implementation for an Output Server."""
    pass


class OutputClient(InputServer):
    """Topic implementation for an Output Client."""
    pass


class LogTopic(Topic):
    """Topic to log all messages."""

    def __init__(self, topic, callback=None):
        logtopic = os.path.join(topic, '#')

        super().__init__(logtopic, callback)


class RequestTopic(object):
    """RequestTopic format."""

    REQUEST_FIELDS = {'clientid', 'requestid'}
    REQUEST_SUFFIX = 'ctl/{command}/request/{clientid}/{requestid}'
    REPLY_SUFFIX = 'ctl/{command}/reply/{clientid}/{requestid}'

    _TOPIC_RE = r'^{}/(request|reply)/{}/{}$'.format(r'(?P<topic>.*)',
                                                     Topic.LEVEL % 'clientid',
                                                     Topic.LEVEL % 'requestid')
    TOPIC_RE = re.compile(_TOPIC_RE)
    TOPIC_REPL_FMT = r'\g<topic>/{0}/\g<clientid>/\g<requestid>'

    @classmethod
    def request_topic(cls, topic, command, **fields):
        """Request topic from topic."""
        topic = os.path.join(topic, cls.REQUEST_SUFFIX)
        topic = common.topic_lazyformat(topic, command=command, **fields)
        return topic

    @classmethod
    def reply_topic(cls, topic, command, **fields):
        """Reply topic for topic."""
        topic = os.path.join(topic, cls.REPLY_SUFFIX)
        topic = common.topic_lazyformat(topic, command=command, **fields)
        return topic

    @classmethod
    def reply_topic_from_request(cls, request_topic):
        """Calculate request reply topic from request topic."""
        topic_repl = cls.TOPIC_REPL_FMT.format('reply')
        return cls.TOPIC_RE.sub(topic_repl, request_topic)

    @classmethod
    def request_topic_from_reply(cls, reply_topic):
        """Calculate request reply topic from request topic."""
        topic_repl = cls.TOPIC_REPL_FMT.format('request')
        return cls.TOPIC_RE.sub(topic_repl, reply_topic)

    @classmethod
    def clean_callback_fields(cls, fields_values):
        """Remove fields that should not be passed to callback."""
        # Remove 'request' fields
        cleaned_fields_values = {k: v for k, v in fields_values.items()
                                 if k not in cls.REQUEST_FIELDS}

        return cleaned_fields_values


class RequestServer(Topic):
    """Topic implementation for a Request server."""

    def __init__(self, topic, command, callback=None):
        assert callback
        request_topic = RequestTopic.request_topic(topic, command)
        super().__init__(request_topic, callback=callback)

    def wrap_callback(self, callback):  # overrides
        """Call topic callback with expanded field values.

        Publish return values to reply_topic.
        """
        @functools.wraps(callback)
        def _wrapper(mqttc, obj, msg):  # pylint:disable=unused-argument
            """Call topic callback with expanded field values.

            Publish return values to reply_topic.
            """
            # Remove 'request/client ids', not given to callback
            fields_values = self.fields_values(msg.topic)
            fields_values = RequestTopic.clean_callback_fields(fields_values)
            reply_topic = RequestTopic.reply_topic_from_request(msg.topic)

            # Add reply_publisher to message
            msg.reply_publisher = mqttc.publisher(reply_topic)

            result = callback(msg, **fields_values)

            # Asynchronous answer
            if result is None:
                return

            # Publish result
            msg.reply_publisher(result)

        return _wrapper


class RequestClient(Topic):
    """Topic implementation for a Request client."""

    REQUEST_TIMEOUT = 30
    REQUEST_ERRORS = {
        'timeout': 'Answer timeout',
        'pubtimeout': 'Request not published before timeout',
    }

    def __init__(self, topic, command, callback=None, clientid=None):
        assert callback is None
        assert clientid is not None

        self.clientid = clientid
        reply_topic = RequestTopic.reply_topic(topic, command,
                                               clientid=clientid)
        super().__init__(reply_topic, callback=callback)

        self.request_topic = RequestTopic.request_topic(topic, command,
                                                        clientid=clientid)
        self.requestid = 0
        self._request_lock = threading.Lock()
        self._request_event = threading.Event()
        self._request_answer = None

    def request(self, client, data, timeout=None, **fields):
        """Perform request under lock and wait for response."""
        with self._request_lock:  # pylint:disable=not-context-manager
            return self._request(client, data, timeout=timeout, **fields)

    def _request(self, client, data, timeout=None, **fields):
        """Perform request, should be called under lock.

        Create a new request by updating request_id.
        Register a callback for current request.
        Then perform blocking request."""
        self.requestid += 1
        topic = self.request_topic.format(requestid=self.requestid, **fields)
        reply_topic = RequestTopic.reply_topic_from_request(topic)

        with client.message_callback(reply_topic, self._cb_request):
            answer = self._do_blocking_request(client, topic, data, timeout)
            return answer

    def _do_blocking_request(self, client, topic, data, timeout=None):
        """Publish request and wait for request answer. Handles timeout."""
        timeout = timeout or self.REQUEST_TIMEOUT

        self._request_event.clear()
        self._request_answer = None

        message = client.publish(topic, data)

        answered = self._request_event.wait(timeout)
        if answered:
            return self._request_answer

        # No answer
        if message.is_published():
            raise RuntimeError(self.REQUEST_ERRORS['timeout'])
        else:
            raise RuntimeError(self.REQUEST_ERRORS['pubtimeout'])

    def _cb_request(self, mqttc, obj, msg):  # pylint:disable=W0221,W0613
        """Callback for request answer. Set answer and release event."""
        self._request_answer = msg.payload
        self._request_event.set()


class ChannelTopic(object):
    """ChannelTopic format."""
    OUTPUT_SUFFIX = 'data/out'
    INPUT_SUFFIX = 'data/in'

    INPUT_RE = re.compile('/%s$' % INPUT_SUFFIX)

    _TOPIC_RE = r'^{}/data/(in|out)'.format(r'(?P<topic>.*)')
    TOPIC_RE = re.compile(_TOPIC_RE)
    TOPIC_REPL = r'\g<topic>'

    @classmethod
    def output_topic(cls, topic):
        """Output topic from topic."""
        topic = os.path.join(topic, cls.OUTPUT_SUFFIX)
        return topic

    @classmethod
    def input_topic(cls, topic):
        """Input topic for topic."""
        topic = os.path.join(topic, cls.INPUT_SUFFIX)
        return topic

    @classmethod
    def output_topic_from_input(cls, input_topic):
        """Calculate output topic from input topic."""
        topic = cls.TOPIC_RE.sub(cls.TOPIC_REPL, input_topic)
        return cls.output_topic(topic)

    @classmethod
    def input_topic_from_output(cls, output_topic):
        """Calculate output topic from output topic."""
        topic = cls.TOPIC_RE.sub(cls.TOPIC_REPL, output_topic)
        return cls.input_topic(topic)


class OutputChannelServer(NullTopic):
    """Topic implementation for a Output only Channel server."""
    def __init__(self, topic, callback=None):
        super().__init__(topic, callback=callback)
        self.output_topic = ChannelTopic.output_topic(topic)

    def output_publisher(self, client, **fmt):
        """Output publisher function for topic formatted with **fmt."""
        topic = self.output_topic.format(**fmt)
        return client.publisher(topic)


class ChannelServer(Topic):
    """Topic implementation for a Channel server."""
    def __init__(self, topic, callback=None):
        input_topic = ChannelTopic.input_topic(topic)
        super().__init__(input_topic, callback=callback)
        self.output_topic = ChannelTopic.output_topic(topic)

    def output_publisher(self, client, **fmt):
        """Output publisher function for topic formatted with **fmt."""
        topic = self.output_topic.format(**fmt)
        return client.publisher(topic)


class ChannelClient(Topic):
    """Topic implementation for a Channel client."""
    def __init__(self, topic, callback=None):
        output_topic = ChannelTopic.output_topic(topic)
        super().__init__(output_topic, callback=callback)
        self.input_topic = ChannelTopic.input_topic(topic)

    def send(self, client, data, **fmt):
        """Send ``data`` to topic formatted with **fmt."""
        topic = self.input_topic.format(**fmt)
        return client.publish(topic, data)


class ErrorTopic(object):
    """ErrorTopic format."""
    ERROR_SUFFIX = 'error/'
    SUBSCRIBE_SUFFIX = 'error/#'

    @classmethod
    def error_topic(cls, topic):
        """Error base topic from topic."""
        topic = os.path.join(topic, cls.ERROR_SUFFIX)
        return topic

    @classmethod
    def subscribe_topic(cls, topic):
        """Error subscribe topic from topic."""
        topic = os.path.join(topic, cls.SUBSCRIBE_SUFFIX)
        return topic

    @staticmethod
    def relative_topic(base_topic, topic):
        """Get relative part from base_topic."""
        if topic.startswith(base_topic):
            return topic.replace(base_topic, '').lstrip('/')
        raise ValueError('Topic %s is not a subtopic from %s' %
                         (topic, base_topic))


class ErrorServer(NullTopic):
    """Topic implementation for an Error server."""

    def __init__(self, topic, callback=None):
        server_topic = ErrorTopic.error_topic(topic)
        super().__init__(server_topic, callback=callback)

        self.base_topic = topic

    def publish_error(self, client, topic, error_payload):
        """Publish ``error_payload`` to error topic for ``topic``."""
        relative_topic = ErrorTopic.relative_topic(self.base_topic, topic)
        error_topic = os.path.join(self.topic, relative_topic)
        client.publish(error_topic, error_payload)


class ErrorClient(Topic):
    """Topic implementation for an Error client."""

    def __init__(self, topic, callback=None):
        subscribe_topic = ErrorTopic.subscribe_topic(topic)
        super().__init__(subscribe_topic, callback=callback)

        self.error_topic = ErrorTopic.error_topic(topic)

    def wrap_callback(self, callback):  # overrides
        """Wrap callback to call it with relative topic."""
        @functools.wraps(callback)
        def _wrapper(mqttc, obj, msg):  # pylint:disable=unused-argument
            rel_topic = ErrorTopic.relative_topic(self.error_topic, msg.topic)
            return callback(msg, rel_topic)

        return _wrapper
