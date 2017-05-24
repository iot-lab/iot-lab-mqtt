# -*- coding: utf-8 -*-

"""Processes management common."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

try:
    import Queue as queue
except ImportError:  # pragma: no cover
    import queue
import os
import time
import threading
import subprocess
import functools

from . import common


def empty_queue(my_queue):
    """Empty message queue."""
    try:
        while True:
            my_queue.get_nowait()
    except queue.Empty:
        return


class Process(object):
    """Process manager."""
    STATES = ['New', 'Running', 'Stopping', 'Stopped']

    def __init__(self, closed_cb, stdout_cb, stderr_cb, error_cb):
        self.callbacks = {
            'closed': closed_cb,
            'stdout': stdout_cb,
            'stderr': stderr_cb,
            'error': error_cb,
        }
        self.state = 'New'
        self.command = None
        self.proc = None
        self.stdin_queue = queue.Queue(0)

        self._threads = {}
        self._rlock = threading.RLock()

    def is_idle(self):
        """Test if current process is not running."""
        return self.state in ('New', 'Stopped')

    @common.synchronized('_rlock')
    def run(self, command):
        """Run given `command`.

        Process should be in an idle state.
        """
        if not self.is_idle():
            return 'Process still running, be stopped before running'

        try:
            self.command = list(command)
            return self._run()
        except OSError as err:
            # Invalid command
            return '%s' % err
        except (TypeError, ValueError) as err:
            # Invalid arguments (maybe if not a list ?)
            return 'Invalid command'

    def _run(self):
        empty_queue(self.stdin_queue)
        self._popen()
        self.state = 'Running'
        return ''

    @common.synchronized('_rlock')
    def poll(self):
        """Check if process has terminated.

        Returns returncode string if there is one else '' or error.
        """
        if self.state == 'New':
            return 'Error process never run'

        if self.state != 'Stopped':
            return ''

        retcode = self.proc.returncode
        retcode = retcode if retcode is not None else ''
        return '%s' % retcode

    @common.synchronized('_rlock')
    def kill(self, timeout=1):
        """Kill current process."""
        if self.state != 'Running':  # Include 'Stopping'
            return ''

        self._kill(timeout=timeout)

        return ''

    def _kill(self, timeout=1):
        """Kill current process.

        Sends terminate then kill if still running after timeout
        """
        try:
            self.proc.terminate()
            self.proc_wait_timeout(self.proc, timeout)
            self.proc.kill()
        except OSError:
            pass

    @staticmethod
    def proc_wait_timeout(proc, timeout, step=0.05):
        """Wait for proc to terminate at max timeout."""
        t_end = time.time() + timeout
        while time.time() < t_end:
            if proc.poll() is not None:
                break
            time.sleep(step)
        return proc.poll()

    @common.synchronized('_rlock')
    def rerun(self):
        """Rerun current process."""
        if self.state == 'New':
            return 'Error process never run'
        if not self.is_idle():
            return 'Process still running, be stopped before running'

        return self._run()

    @common.synchronized('_rlock')
    def write(self, data):
        """Write data to process stdin."""
        if self.state == 'New':
            self.callbacks['error']('Process not running')
            return

        if self.state != 'Running':
            # Ignore here, no error as it could happen dynamically
            return

        self.stdin_queue.put(data)

    def _popen(self):
        # Set PYTHONUNBUFFERED as its our major language
        # And it will be used by agents
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'

        popen_kwargs = {
            'stdin': subprocess.PIPE,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'shell': False,
            'close_fds': False,
            'env': env,
        }

        self.proc = subprocess.Popen(args=self.command, **popen_kwargs)
        self._threads['stdout'] = self._pipe_reader(
            'stdout', self.proc.stdout, self.callbacks['stdout'])
        self._threads['stderr'] = self._pipe_reader(
            'stderr', self.proc.stderr, self.callbacks['stderr'])
        self._threads['stdin'] = self._pipe_writer(
            'stdin', self.proc.stdin, self.stdin_queue)

    @common.synchronized('_rlock')
    def _handle_thread_end(self, name):
        """Handle current thread closing.

        On all thread closed, return.
        """
        self._threads.pop(name, None)
        if self._threads:
            self.state = 'Stopping'
            return

        # No more threads
        self.state = 'Stopped'
        self.callbacks['closed'](self.proc.returncode)

    def _pipe_reader(self, name, pipe, data_handler):
        """Reader from a pipe to data_handler."""
        args = (name, pipe, data_handler)
        thr = threading.Thread(target=self._pipe_reader_thr, args=args)
        thr.start()
        return thr

    def _pipe_reader_thr(self, name, pipe, data_handler, delay=0.1):
        """Thread target for reader from a pipe to data_handler."""
        self._set_nonblocking(pipe)
        while self._pipe_read_and_handle(pipe, data_handler, delay=delay):
            pass
        self._handle_thread_end(name)

    def _pipe_read_and_handle(self, pipe, data_handler, delay=0.1):
        """Try reading from pipe and handle data if any available.

        :returns: True if there can still be some data to read
        """
        try:
            data = pipe.read(1024)
        except IOError:
            data = ''

        if data:
            data_handler(data)
            return True

        if self.proc.poll() is None:
            time.sleep(delay)
            return True

        # No data and proc is dead
        # Send a last empty message
        data_handler(b'')
        return False

    @staticmethod
    def _set_nonblocking(pipe):
        """Set supbrocess pipe non blocking."""
        import fcntl
        flags = fcntl.fcntl(pipe, fcntl.F_GETFL)
        fcntl.fcntl(pipe, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def _pipe_writer(self, name, pipe, data_queue):
        """Writer to a pipe from data_queue."""
        args = (name, pipe, data_queue)
        thr = threading.Thread(target=self._pipe_writer_thr, args=args)
        thr.start()
        return thr

    def _pipe_writer_thr(self, name, pipe, data_queue, timeout=1):
        """Thread target for writer to a pipe from data_queue."""
        while self.proc.poll() is None:
            self._queue_get_and_write_pipe(pipe, data_queue, timeout=timeout)

        # Cleanup
        empty_queue(data_queue)

        self._handle_thread_end(name)

    @staticmethod
    def _queue_get_and_write_pipe(pipe, data_queue, timeout=1):
        """Get message from `data_queue` and write it to `pipe`."""
        try:
            data = data_queue.get(True, timeout)
            pipe.write(data)
            pipe.flush()
        except queue.Empty:
            pass
        except IOError:
            # write failed should be handled outside with proc.poll()
            pass


class ProcessManager(dict):
    """Process manager dict. Handles process by names."""

    def __init__(self, callbacks):
        super().__init__()
        self.process_callbacks = callbacks
        self._pid = 0
        self._rlock = threading.RLock()

    def start(self):
        """Start ProcessManager."""
        # Nothing to do currently
        pass

    def stop(self, timeout=5, step=0.05):
        """Stop ProcessManager.

        Kills all processes and wait for them to finish.
        """
        # First kill all before using timeout
        self._killall()

        t_end = time.time() + timeout
        while time.time() < t_end:
            if self._trystop():
                break
            time.sleep(step)

    def _trystop(self):
        """Try stopping all processes."""
        self._killall()
        return self._safefreeall()

    def _killall(self):
        """Kill all processes."""
        for proc in self.values():
            proc.kill()

    def _safefreeall(self):
        """Safe free all idle processes. Returns if all are freed."""
        for name in list(self.keys()):
            self.safefree(name)
        return not bool(self)

    @common.synchronized('_rlock')
    def new(self, name=''):
        """Allocate a new uniq process name.

        :param name: if provided, try using it, raise an error if already used
        """
        if not name:
            name = self._new_pid()
        name = str(name)

        if name in self:
            raise ValueError('name %s already in use' % name)

        self[name] = self._new_process(name)

        return name

    def _new_pid(self):
        # Increment to find a new PID
        while True:
            self._pid += 1
            pid = str(self._pid)
            if pid not in self:
                break

        return pid

    def _new_process(self, name):
        """Create a new process for `name`."""
        cb_with_name = [functools.partial(cb, name) for cb in
                        self.process_callbacks]
        return Process(*cb_with_name)

    @common.synchronized('_rlock')
    def free(self, name):
        """Free given process name process if idle."""
        proc = self[name]

        if not proc.is_idle():
            raise RuntimeError('Process still running wait or kill it first')

        self.pop(name)

    @common.synchronized('_rlock')
    def safefree(self, name):
        """Free given process name process if idle. Ignore if still running."""
        try:
            self.free(name)
        except RuntimeError:
            pass

    @common.synchronized('_rlock')
    def list(self):
        """List all processes."""
        return sorted(self.keys())
