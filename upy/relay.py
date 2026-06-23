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

import asyncio
import network
import espnow
import time
import ubinascii

from colorama import Fore, Style
from colors import *
from event import *
from component import Component
from config_error import ConfigurationError

class Relay(Component):
    NAME = 'relay'

    def __init__(self, config=None, message_factory=None, pixel=None):
        '''
        Initializes network interfaces and injects the centralized message factory.
        '''
        Component.__init__(self, Relay.NAME, suppressed=False, enabled=True)
        self._message_factory = message_factory
        self._pixel = pixel
        # load device list from configuration ┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._config = config
        _cfg = self._config['relay']
        self._verbose = _cfg['verbose']
        self._log.info("verbose: {}".format(self._verbose))
        self._device_list = _cfg.get('devices', [])
        self._total_devices = len(self._device_list)
        self._log.info('loaded configuration for:   ' + Fore.GREEN + '{} devices.'.format(self._total_devices))
        # establish network ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)
        # determine local MAC address ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        _local_mac_bytes = self._wlan.config('mac')
        self._local_mac_str = ubinascii.hexlify(_local_mac_bytes, ':').decode('utf-8')
        self._log.info('booting device MAC address: ' + Fore.GREEN + '{}'.format(self._local_mac_str))
        # find this device's position in catalog ┈┈┈┈┈┈┈┈┈┈┈
        self._index = None # index of this device
        for i, device in enumerate(self._device_list):
            if device.get('mac').lower() == self._local_mac_str.lower():
                self._index = i
                break
        if self._index is None:
            self._pixel.show_color(COLOR_RED)
            raise ConfigurationError("local MAC address '{}' not found in topology catalog.".format(self._local_mac_str))
        else:
            self._pixel.show_color(COLOR_DEEP_CYAN)
            self._log.info('this device identified as:  '
                    + Fore.GREEN + '{}'.format(self._device_list[self._index].get('name')))
        # configure relay routing map ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._upstream_mac   = None
        self._downstream_mac = None
        self._is_endpoint    = False
        self._build_routing_map()
        # if this is first node, set up Initiator ┈┈┈┈┈┈┈┈┈┈
        self._initiator = None
        if self._index == 0:
            self._establish_initiator()
        # set up ESP32-NOW ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._espnow = espnow.ESPNow()
        self._espnow.active(True)
        self._espnow.config(timeout_ms=10)
        self._rx_callback    = None
        self._led_task       = None
        # register peers ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        if self._upstream_mac:
            self._espnow.add_peer(self._upstream_mac)
        if self._downstream_mac:
            self._espnow.add_peer(self._downstream_mac)
        if self.enabled:
            self._log.info(Fore.GREEN + 'ready.')
        else:
            self._log.info(Fore.RED + 'disabled.')

    @property
    def index(self):
        '''
        Return the index number of this device within the relay.
        '''
        return self._index

    @property
    def upstream_mac(self):
        '''
        Return the MAC address of the upstream device in the relay.
        '''
        return self._upstream_mac

    @property
    def downstream_mac(self):
        '''
        Return the MAC address of the downstream device in the relay.
        '''
        return self._downstream_mac

    def _establish_initiator(self):
        '''
        Set up push button to trigger messages.
        '''
        self._log.info("establishing initiator…")

        from initiator import Initiator

        self._initiator = Initiator(self._config, self)

    def _build_routing_map(self):
        '''
        Build neighbor routing maps and display to console.
        '''
        # disable device if configuration flag is False
        if self._device_list[self._index].get('enabled') is False:
            self.disable()
        upstream_name = "None"
        downstream_name = "None"
        # scan backwards to find the first enabled upstream neighbor
        for i in range(self._index - 1, -1, -1):
            device = self._device_list[i]
            if device.get('enabled', True):
                _mac_address = device.get('mac')
                self._upstream_mac = self._mac_to_bytes(_mac_address)
                upstream_name = Fore.GREEN + device.get('name')
                break
        # scan forwards to find the first enabled downstream neighbor
        for i in range(self._index + 1, self._total_devices):
            device = self._device_list[i]
            if device.get('enabled', True):
                _mac_address = device.get('mac')
                self._downstream_mac = self._mac_to_bytes(_mac_address)
                downstream_name = Fore.GREEN + device.get('name')
                break
        else:
            self._is_endpoint = True
        # determine role label for console output
        if not self.enabled:
            role_label = Fore.RED + "DISABLED"
            self.disable()
        elif self._index == 0:
            role_label = Fore.GREEN + "INITIATOR"
        elif self._is_endpoint:
            role_label = Fore.GREEN + "ENDPOINT"
        else:
            role_label = Fore.GREEN + "RELAY NODE"
        self._log.info("topology routing resolved:")
        self._log.info("  ├─ Role:       {}".format(role_label))
        self._log.info("  ├─ Upstream:   {}".format(upstream_name))
        self._log.info("  └─ Downstream: {}".format(downstream_name))

    def set_receive_callback(self, callback):
        self._rx_callback = callback

    def send_message(self, peer, direction, message):
        '''
        Serializes an existing Message instance and transmits it over the network.
        '''
        if self._verbose:
            self._log.info('sending message in {} direction: {}'.format(direction, message))
        payload = "{},{},{}".format(
            direction,
            message.event.label,
            message.value if message.value is not None else ""
        )
        self._espnow.send(peer, payload.encode('utf-8'))

    def process_endpoint_logic(self, incoming_message):
        '''
        Executes operations on the last Node and requests a new message from the factory.
        '''
        _value = incoming_message.value
        if self._verbose:
            self._log.info('processing endpoint logic for message: '
                    + Fore.GREEN + '{}'.format(incoming_message))
        else:
            self._log.info('inbound message: ' + Fore.GREEN + '{}'.format(_value))
        # reverse string
        response_value = self._reverse_string(_value)
        # or prepend 'processed' to string
#       response_value = "processed: {}".format(_value)
        self._log.info('outbound message: ' + Fore.GREEN + '{}'.format(response_value))
        return self._message_factory.create_message(
            event=RELAY,
            value=response_value
        )

    def handle_outbound(self, message):
        '''
        Handles messages moving down the chain toward the endpoint (Node 5).
        '''
        if self._led_task:
            self._led_task.cancel()
        if self._is_endpoint:
            if self._verbose:
                self._log.info('handling outbound message at endpoint: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_TANGERINE, 3000))
            response_msg = self.process_endpoint_logic(message)
            if self._upstream_mac:
                self.send_message(self._upstream_mac, -1, response_msg)
        else:
            if self._verbose:
                self._log.info('handling outbound message: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_SKY_BLUE, 500))
            if self._downstream_mac:
                self.send_message(self._downstream_mac, 1, message)

    def handle_inbound(self, message):
        '''
        Handles messages moving up the chain back toward the initiator (Node 1).
        '''
        if self._upstream_mac:
            if self._verbose:
                self._log.info('handling inbound message: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_DEEP_FUCHSIA, 500))
            self.send_message(self._upstream_mac, -1, message)
        else:
            if self._verbose:
                self._log.info("initiator received ricochet response: {}".format(repr(message)))
            if self._rx_callback:
                self._rx_callback(message)
            self._led_task = asyncio.create_task(self._flash_led(COLOR_APPLE, 3000))

    async def run_loop(self):
        '''
        Asynchronous polling loop that processes incoming packets without blocking.
        '''
        while True:
            # check for incoming ESP-NOW packets
            host, msg = self._espnow.recv()
            if msg:
                try:
                    decoded_msg = msg.decode('utf-8')
                    parts = decoded_msg.split(',', 2)
                    if len(parts) < 3:
                        continue
                    direction = int(parts[0])
                    event_label = parts[1]
                    raw_value = parts[2]
                    value_payload = raw_value if raw_value != "" else None
                    reconstructed_msg = self._message_factory.create_message(
                        event=RELAY,
                        value=value_payload
                    )
                    if direction == 1:
                        self.handle_outbound(reconstructed_msg)
                    elif direction == -1:
                        self.handle_inbound(reconstructed_msg)
                except Exception as e:
                    self._log.error('error in relay: {}'.format(e))
            # yield control back to the asyncio scheduler
            await asyncio.sleep_ms(5)

    # utility methods ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    async def _flash_led(self, color, duration_ms=1000):
        self._pixel.show_color(color)
        await asyncio.sleep_ms(duration_ms)
        self._pixel.show_color(COLOR_BLACK)

    def _reverse_string(self, value):
        '''
        Reverse the characters in the argument.
        '''
        return ''.join(reversed(value))

    def _mac_to_bytes(self, mac_str):
        '''
        Converts a colon-separated hex MAC string into a bytes object.
        '''
        clean_hex = mac_str.replace(':', '')
        return ubinascii.unhexlify(clean_hex)

#EOF
