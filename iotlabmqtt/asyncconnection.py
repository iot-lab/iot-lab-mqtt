# -*- coding: utf-8 -*-

"""Asyncore Service and connection implementation.

Implement a class for AsyncoreService and a NodeConnection with handlers.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import socket
import threading
import asyncore


class RawHandler(object):  # pylint:disable=too-few-public-methods
    """Raw data handler."""
    def __init__(self, handler):
        self.handler = handler

    def __call__(self, data):
        """Call handler on raw data."""
        self.handler(data)


class NodeConnection(asyncore.dispatcher_with_send):
    """Handle the asyncore connection to one node."""

    RECV_LEN = 8192

    def __init__(self, archi, num,  # pylint:disable=too-many-arguments
                 event_handler, data_handler=None, service=None):
        asyncoremap = getattr(service, 'map', None)
        asyncore.dispatcher_with_send.__init__(self, map=asyncoremap)

        self.address = self._address(archi, num)

        self.event_handler = event_handler
        self.data_handler = data_handler

    def _address(self, archi, num):  # pylint:disable=no-self-use
        """Return socket address for archi/num."""
        return archi, int(num)

    def handle_data(self, data):
        """Call given data_handler."""
        # save value for thread safety, data_handler can change
        handler = self.data_handler
        if handler:
            handler(data)

    def start(self):
        """Connects to node serial port:"""

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.connect(self.address)
        except:  # pylint:disable=broad-except,bare-except
            self.handle_error()

    def handle_connect(self):
        """Node connected."""
        self.event_handler('connect')

    def handle_close(self):
        """Close the connection and clear buffer."""
        self.close()
        self.event_handler('close')

    def close(self):
        """Safe close."""
        try:
            asyncore.dispatcher_with_send.close(self)
        except AttributeError:
            # When close is done on socket == None
            pass

    def handle_read(self):
        """Read bytes and run data handler."""
        data = self.recv(self.RECV_LEN)
        self.handle_data(data)

    def handle_error(self):
        """Error."""
        self.event_handler('error')


class AsyncoreService(object):
    """Asyncore wrapping in a Thread."""
    ASYNCORE_LOOP_KWARGS = {'timeout': 1, 'use_poll': True}

    def __init__(self):
        self.keep_alive = None
        self.map = {}
        self.thread = threading.Thread(target=self._loop)
        self.thread.deamon = True

    def start(self):
        """Start service.

        Register a 'keep_alive' dispatcher to maintain asyncore loop.
        Start asyncore loop in a thread.
        """
        self.keep_alive = self._keep_alive_dispatcher(self.map)
        self.thread.start()

    def _loop(self):
        """Run asyncore loop."""
        args = {'map': self.map}
        args.update(self.ASYNCORE_LOOP_KWARGS)
        return asyncore.loop(**args)

    def stop(self):
        """Stop service.
        All nodes connection should be closed before.

        Close the keep_alive and wait for thread to return.
        """
        self.keep_alive.close()
        self.thread.join()

    @staticmethod
    def _keep_alive_dispatcher(asyncoremap=None):
        """Stub tcp dispatcher to keep asyncore looping."""
        dispatcher = asyncore.dispatcher(map=asyncoremap)
        dispatcher.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        dispatcher.set_reuse_addr()
        dispatcher.bind(('', 0))
        dispatcher.listen(0)
        return dispatcher
