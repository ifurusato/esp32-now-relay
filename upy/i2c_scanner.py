#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-01-27
# modified: 2026-06-04

from colorama import Fore, Style

class I2CScanner:
    '''
    Args:
        i2c:   the instantiated I2C bus
    '''
    def __init__(self, i2c=None):
        self._i2c     = i2c
        self._devices = []
        # ready.

    @property
    def devices(self):
        '''
        Return the scanned list of devices.
        '''
        self._devices = []

    def scan(self):
        '''
        Scan all valid 7-bit I2C addresses, returning a list of found addresses.
        '''
        print(Fore.CYAN + Style.DIM + 'starting I2C scan…' + Style.RESET_ALL)
        self._devices = self._i2c.scan()
        if len(self._devices) == 0:
            print(Fore.CYAN + 'no I2C devices found.' + Style.RESET_ALL)
        else:
            print(Fore.CYAN + 'I2C scan complete: ' + Fore.GREEN + '{} devices found.'.format(len(self._devices)) + Style.RESET_ALL)
        return self._devices

    def has_hex_address(self, address):
        '''
        Returns True if a given address is in the scanned device list.
        '''
        return address in self._devices

    def i2cdetect(self, color=Fore.CYAN):
        '''
        Display I2C device addresses in i2cdetect format to stdout.
        Scans if not already done, then prints a formatted grid.
        '''
        if not self._devices:
            self.scan()
        print(color)
        # print header
        print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
        # print each row (0x00-0x70 in steps of 0x10)
        for row in range(0x00, 0x80, 0x10):
            print("{:02x}:".format(row), end='')
            for col in range(0x10):
                addr = row + col
                if addr < 0x08 or addr > 0x77:
                    # invalid I2C address range
                    print("   ", end='')
                elif addr in self._devices:
                    print(" {:02x}".format(addr), end='')
                else:
                    print(" --", end='')
            print()  # newline at end of row
        print(Style.RESET_ALL)

#EOF
