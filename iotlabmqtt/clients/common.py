# -*- coding: utf-8 -*-

"""IoT-LAB MQTT client common"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os
import sys
import uuid
import readline
import functools


def async_print_handle_readlinebuff(cmd_obj):
    """Manages a clean readline buffer for asynchronous print.

    If there is content in readline buffer, add a newline before calling
    function and restore readline displayed string after function.
    """
    def _wrap(func):
        @functools.wraps(func)
        def _wrapped(*args, **kwargs):

            if readline.get_line_buffer():
                print()

            ret = func(*args, **kwargs)

            sys.stdout.write(cmd_obj.prompt)
            sys.stdout.write(readline.get_line_buffer())
            sys.stdout.flush()
            return ret

        return _wrapped
    return _wrap


def clientid(name=None):
    """Return clientid for ``name``.

    If ``name`` is None, use hostname.
    """
    name = name or os.uname()[1]
    return '%s-%s' % (name, uuid.uuid4())
