#! /usr/bin/env python
# -*- coding:utf-8 -*-
"""Print 'Message' and wait for signal."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import signal


def main():
    """Print 'Message' and wait for signal."""
    print('Message')
    signal.pause()


if __name__ == '__main__':
    main()
