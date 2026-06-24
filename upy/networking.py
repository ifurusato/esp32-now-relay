#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-22
# modified: 2026-06-23

import network
import espnow
import ubinascii

from colorama import Fore, Style
from logger import Logger, Level

class Networking:
    NAME = 'network'

    def __init__(self, level=Level.INFO):
        '''
        Initializes network interfaces and sets up ESP32-NOW.
        '''
        self._log = Logger('network', level=level)
        # establish network ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)
        # determine local MAC address ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        _local_mac_bytes = self._wlan.config('mac')
        self._local_mac_str = ubinascii.hexlify(_local_mac_bytes, ':').decode('utf-8')
        self._log.info('booting device MAC address: ' + Fore.GREEN + '{}'.format(self._local_mac_str))
        # set up ESP32-NOW ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._espnow = espnow.ESPNow()
        self._espnow.active(True)
        self._espnow.config(timeout_ms=2)
        self._log.info('ready.')

    @property
    def mac_address(self):
        '''
        Return the MAC address of this device.
        '''
        return self._local_mac_str

    @property
    def espnow(self):
        '''
        Return the ESP32-NOW implementation.
        '''
        return self._espnow

#EOF
