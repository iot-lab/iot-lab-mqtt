# -*- coding: utf-8 -*-

"""Clients for IoT-LAB MQTT agents"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

from . import serial
from . import radiosniffer


PARSER = argparse.ArgumentParser()
SUBPARSER = PARSER.add_subparsers(dest='command')
SUBPARSER.required = True

# Add parser that use given module parser
#   'add_help=False' prevents '--help' duplicate
SUBPARSER.add_parser('serial', parents=[serial.PARSER], add_help=False,
                     help='serial redirection client')
SUBPARSER.add_parser('radiosniffer', parents=[radiosniffer.PARSER],
                     add_help=False, help='radiosniffer client')


def main():
    """Run given client main function."""
    opts = PARSER.parse_args()
    client = globals()[opts.command]
    client.main(opts)
