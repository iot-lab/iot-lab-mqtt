# -*- coding:utf-8 -*-

"""Common functions for iotlabmqtt agents."""


from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622


import string


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


def clientid(name=None):
    """Return clientid for ``name``.

    If ``name`` is None, use hostname.
    """
    import os
    import uuid
    name = name or os.uname()[1]
    return '%s-%s' % (name, uuid.uuid4())
