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
        self._max_data_len = espnow.MAX_DATA_LEN
        if self._max_data_len > 250:
            self._espnow_version = 2.0
        else:
            self._espnow_version = 1.0
        self._log.info('using ESP-NOW V{} with maximum data length of {} bytes.'.format(self._espnow_version, self._max_data_len))
        self._espnow.config(timeout_ms=0)
        self._log.info('ready.')

    @property
    def version(self):
        '''
        Returns the ESP-NOW version, V1.0 or V.20. Packet limit lengths are respectively 250 and 1470 bytes.
        '''
        return self._espnow_version

    @property
    def max_data_len(self):
        '''
        Returns the ESP-NOW maximum data length, V1.0 is 250 bytes, V2.0 is 1470 bytes.
        '''
        return self._max_data_len

    def stats(self):
        '''
        Return the statistics available from ESP-NOW as a tuple:
            tx_pkts, tx_responses, tx_failures, rx_packets, rx_dropped_packets
        '''
        tx_pkts, tx_responses, tx_failures, rx_packets, rx_dropped_packets = self._espnow.stats()
        return tx_pkts, tx_responses, tx_failures, rx_packets, rx_dropped_packets

    def peers_table(self):
        '''
        Returns the peer device table, a dict of known peer devices and RSSI values:

            {peer: [rssi, time_ms], ...}

        where:

            peer is the peer MAC address (as bytes);
            rssi is the wifi signal strength in dBm (-127 to 0) of the last message received from the peer; and
            time_ms is the time the message was received (in milliseconds since system boot - wraps every 12 days).
        '''
        return self._espnow.peers_table

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
