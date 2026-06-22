#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-22
# modified: 2026-06-22

import asyncio
import network
import espnow
import time

from colorama import Fore, Style
from colors import *
from event import *
from component import Component

class Relay(Component):
    NAME = 'relay'

    def __init__(self, message_factory=None, pixel=None, upstream_mac=None, downstream_mac=None, is_endpoint=False):
        '''
        Initializes network interfaces and injects the centralized message factory.
        '''
        Component.__init__(self, Relay.NAME, suppressed=False, enabled=True)
        self._message_factory = message_factory
        self._pixel = pixel
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.e = espnow.ESPNow()
        self.e.active(True)
        self.e.config(timeout_ms=10)
        self.upstream_mac    = upstream_mac
        self.downstream_mac  = downstream_mac
        self._is_endpoint    = is_endpoint
        self._rx_callback    = None
        self._led_task       = None
        # register peers
        if self.upstream_mac:
            self.e.add_peer(self.upstream_mac)
        if self.downstream_mac:
            self.e.add_peer(self.downstream_mac)
        self._log.info('ready.')

    def set_receive_callback(self, callback):
        self._rx_callback = callback

    def send_message(self, peer, direction, message):
        '''
        Serializes an existing Message instance and transmits it over the air.
        '''
        self._log.info('sending message in {} direction: {}'.format(direction, message))
        payload = "{},{},{}".format(
            direction,
            message.event.label,
            message.value if message.value is not None else ""
        )
        self.e.send(peer, payload.encode('utf-8'))

    def process_endpoint_logic(self, incoming_message):
        '''
        Executes operations on Node 5 and requests a new message from the factory.
        '''
        self._log.info('processing endpoint logic for message: {}'.format(incoming_message))
        response_value = "Processed: {}".format(incoming_message.value)
        # enforce the Factory pattern strictly for the ricochet message generation
        return self._message_factory.create_message(
            event=RELAY,
            value=response_value
        )

    async def _flash_led(self, color, duration_ms=1000):
        self._pixel.show_color(color)
        await asyncio.sleep_ms(duration_ms)
        self._pixel.show_color(COLOR_BLACK)

    def handle_outbound(self, message):
        '''
        Handles messages moving down the chain toward the endpoint (Node 5).
        '''
        if self._led_task:
            self._led_task.cancel()
        if self._is_endpoint:
            self._log.info('handling outbound message at endpoint: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_TANGERINE, 3000))
            response_msg = self.process_endpoint_logic(message)
            if self.upstream_mac:
                self.send_message(self.upstream_mac, -1, response_msg)
        else:
            self._log.info('handling outbound message: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_SKY_BLUE, 500))
            if self.downstream_mac:
                self.send_message(self.downstream_mac, 1, message)

    def handle_inbound(self, message):
        '''
        Handles messages moving up the chain back toward the initiator (Node 1).
        '''
        if self.upstream_mac:
            self._log.info('handling inbound message: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_DEEP_FUCHSIA, 500))
            self.send_message(self.upstream_mac, -1, message)
        else:
            self._log.info("initiator received ricochet response: {}".format(repr(message)))
            if self._rx_callback:
                self._rx_callback(message)
            self._led_task = asyncio.create_task(self._flash_led(COLOR_GREEN, 3000))

    async def run_loop(self):
        '''
        Asynchronous polling loop that processes incoming packets without blocking.
        '''
        while True:
            # check for incoming ESP-NOW packets
            host, msg = self.e.recv()
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

#EOF
