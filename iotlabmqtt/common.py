# -*- coding:utf-8 -*-

"""Common functions for iotlabmqtt agents."""


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622


import sys
import signal
import string
import argparse


def topic_lazyformat(topic, **kwargs):
    u"""Format only replace values in 'kwargs' keeping the other intact.


    >>> topic_lazyformat('a/{b}/c/{d}/e') == 'a/{b}/c/{d}/e'
    True

    >>> topic_lazyformat('a/{b}/c/{d}/e', b='B', any='value') == 'a/B/c/{d}/e'
    True

    >>> topic_lazyformat('a/{b}/c/{d}/e', b='B', d='D') == 'a/B/c/D/e'
    True
    """
    fields = topic_fields(topic)
    # identity formats
    fmt = {f: '{%s}' % f for f in fields}

    # overwrite this ones
    for name, value in kwargs.items():
        fmt[name] = value

    return topic.format(**fmt)


def topic_fields(topic):
    u"""Extract named fields from topic.

    >>> topic_fields('{archi}/{num}/line/{clientid}/{requestid}')
    ['archi', 'num', 'clientid', 'requestid']

    >>> topic_fields('topic/super/cool')
    []

    # Invalid topics

    >>> topic_fields('a/b/{c}/{c}')
    Traceback (most recent call last):
    ValueError: Named fields should be appear only once

    >>> topic_fields('a/{0}/b')
    Traceback (most recent call last):
    ValueError: Use only simple named fields

    >>> topic_fields('a/{}/b')
    Traceback (most recent call last):
    ValueError: Use only simple named fields

    >>> topic_fields('a/{self.test}/b')
    Traceback (most recent call last):
    ValueError: Use only simple named fields

    >>> topic_fields('a/{first}{second}/b')
    Traceback (most recent call last):
    ValueError: There should be only one named field per level

    >>> topic_fields('{name!r}')
    Traceback (most recent call last):
    ValueError: There should be no format or conversion
    """
    fmt = string.Formatter()

    # Prepend with '/' so all fiels have `text` ending with '/'
    _topic = '/' + topic
    fields = [str(name) for text, name, spec, conv in fmt.parse(_topic)
              if _is_named_field(text, name, spec, conv)]
    if len(fields) != len(set(fields)):
        raise ValueError('Named fields should be appear only once')
    return fields


def _is_named_field(text, name, spec, conversion):
    """Return if current field is a named one."""
    # Not a field, just end of the string
    if name is None:
        return False

    # Invalid formats
    if not name or name.isdigit() or '.' in name:
        raise ValueError('Use only simple named fields')
    if not text.endswith('/'):
        raise ValueError('There should be only one named field per level')
    if spec or conversion:
        raise ValueError('There should be no format or conversion')

    return True


class MQTTAgentArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with common agents arguments."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_common_arguments()

    def _add_common_arguments(self):
        """Add common agents arguments to parser."""
        self.add_argument('--prefix', help='Topics prefix', default='')
        self.add_argument('--broker-port', help='Broker port')
        self.add_argument('broker', help='Broker address')


def traceback_error():
    """Get error from traceback to return as answer."""
    return '%s' % (sys.exc_info()[1],)


def synchronized(lockname):
    """Method decorator to synchronize method calls.

    Class should define a lock object at attribute named ``SYNCHRONIZEDATTR``

    http://caffeinatedideas.com/2014/12/12/java-synchronized-in-python.html
    """
    import functools

    def _wrapper(method):
        @functools.wraps(method)
        def _synchronized_method(self, *args, **kwargs):
            with getattr(self, lockname):
                return method(self, *args, **kwargs)
        return _synchronized_method
    return _wrapper


def wait_sigint():
    """Pause until Ctrl+C."""
    try:
        signal.pause()
    except KeyboardInterrupt:
        pass
