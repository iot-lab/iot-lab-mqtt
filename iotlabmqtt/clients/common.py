# -*- coding: utf-8 -*-

"""IoT-LAB MQTT client common"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os
import re
import cmd
import sys
import uuid
import readline
import functools


def clientid(name=None):
    """Return clientid for ``name``.

    If ``name`` is None, use hostname.
    """
    name = name or os.uname()[1]
    return '%s-%s' % (name, uuid.uuid4())


class CmdShell(cmd.Cmd, object):
    """Cmd shell class that handles string as utf8 strings."""

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.input_encoding = sys.stdin.encoding

    def onecmd(self, line):
        """onecmd command wrapped to nicely handle lines and ValueError.

        * decode lines as using stdin encoding
        * replace nbsp in lines
        * Print help on ValueError
        * Print error on RuntimeError
        """
        try:
            line = self.decode_line(line, encoding=self.input_encoding)
            line = self.replace_nbsp(line)
            return cmd.Cmd.onecmd(self, line)

        except UnicodeDecodeError:
            print('Error while decoding input as utf-8')
            return 0

        except ValueError:
            # Error from do_command while handling `arg`
            command = self.parseline(line)[0]
            print('Error: Invalid arguments')
            self._print_usage(command)

        except RuntimeError as err:
            # Error from command execution, ex requests
            print('%s' % err)

    def _print_usage(self, command):
        """Print usage for command."""
        help_func = getattr(self, 'help_' + command)
        print('Usage: ', end='')
        help_func()

    @staticmethod
    def decode_line(line, encoding='utf-8'):
        """Decode ``line`` if is type ``bytes``.

        Allows managing arguments for both python2 and python3.
        cmd uses bytes in python2 and unicode string in python3
        """
        if isinstance(line, bytes):
            line = line.decode(encoding)
        return line

    @staticmethod
    def replace_nbsp(line):
        """Replace non breakable spaces by spaces."""
        return line.replace('\u00A0', ' ')

    @staticmethod
    def cmd_split(arg, maxsplit=0):
        """Split given command arg on whitespaces.

        Cannot use shlex.split as it has issues with unicode strings.
        """
        return re.split(r'\s+', arg, maxsplit=maxsplit)

    def async_print_handle_readlinebuff(self):
        """Manages a clean readline buffer for asynchronous print.

        If there is content in readline buffer, add a newline before calling
        function and restore readline displayed string after function.
        """
        def _wrap(func):
            @functools.wraps(func)
            def _wrapped(*args, **kwargs):

                if readline.get_line_buffer():
                    sys.stdout.write('\n')

                ret = func(*args, **kwargs)

                sys.stdout.write(self.prompt)
                sys.stdout.write(readline.get_line_buffer())
                sys.stdout.flush()
                return ret

            return _wrapped
        return _wrap


def parser_add_site_arg(parser, group_help='Server agent IoT-LAB site name'):
    """Add server agent IoT-LAB site name argument."""
    group = parser.add_argument_group(group_help)
    group.add_argument('--site', help='Server agent site', required=True)
