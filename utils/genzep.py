#! /usr/bin/env python
# -*- coding:utf-8 -*-
"""Periodically print ZEP messages with a timer."""

import sys
import time
import binascii


# pylint:disable=redefined-builtin,invalid-name,no-member
try:
    # Python3
    sys.stdout = sys.stdout.buffer
except AttributeError:
    pass
# pylint:enable=redefined-builtin,invalid-name,no-member


ZEP_MESSAGE_STR = (
    '45 58 02 01'   # Base Zep header
    '0B 00 01 00 ff'   # chan | dev_id | dev_id| LQI/CRC_MODE |  LQI

    '83 aa 7e 80'   # Timestamp msb (Epoch 1/1/1970)
    '00 00 00 00'   # timestamp lsp

    '00 00 00 01'   # seqno

    '00 01 02 03'   # reserved 0-3/10
    '04 05 16 07'   # reserved 4-7/10
    '08 09'         # reserved 8-9 / 10
    '08'            # Length 2 + data_len
    '61 62 63'      # Data
    '41 42 43'      # Data
    'FF FF'         # CRC)
)
ZEP_MESSAGE = binascii.a2b_hex(''.join(ZEP_MESSAGE_STR.split()))


def zep_packet():
    """Return a ZEP packet."""
    # Only a fixed one here
    return ZEP_MESSAGE


def main():
    """Print packets on new line input."""
    try:
        delay = int(sys.argv[1])
    except (TypeError, IndexError):
        delay = 10

    while True:
        time.sleep(delay)
        pkt = zep_packet()

        sys.stderr.write('Writing message: %u\n' % len(pkt))
        sys.stdout.write(pkt)
        sys.stdout.flush()


if __name__ == '__main__':
    main()
