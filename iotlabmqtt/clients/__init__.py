# -*- coding: utf-8 -*-

"""Clients for IoT-LAB MQTT agents"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

from . import serial
from . import node
from . import radiosniffer
from . import process
from . import log


PARSER = argparse.ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='command')
SUBPARSER.required = True

# Add parser that use given module parser
#   'add_help=False' prevents '--help' duplicate
SUBPARSER.add_parser('serial', parents=[serial.PARSER], add_help=False,
                     help='serial redirection client')
SUBPARSER.add_parser('node', parents=[node.PARSER],
                     add_help=False, help='node client')
SUBPARSER.add_parser('radiosniffer', parents=[radiosniffer.PARSER],
                     add_help=False, help='radiosniffer client')
SUBPARSER.add_parser('process', parents=[process.PARSER],
                     add_help=False, help='process client')
SUBPARSER.add_parser('log', parents=[log.PARSER],
                     add_help=False, help='log messages')


def main():
    """Run given client main function."""
    opts = PARSER.parse_args()
    client = globals()[opts.command]
    client.main(opts)
