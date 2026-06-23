#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-23
# modified: 2026-06-23

import time

from colorama import Fore, Style
from logger import Logger, Level
from event import *
from component import Component
from push_button import PushButton
from food_name_generator import FoodNameGenerator

class Initiator(Component):
    NAME = 'initiator'
    '''
    Handles physical button interaction for Node 0 to trigger and measure
    the round-trip time of a network message chain.
    '''
    def __init__(self, config=None, relay_node=None, level=Level.INFO):
        Component.__init__(self, Initiator.NAME, suppressed=False, enabled=True, level=level)
        _cfg = config['initiator']
        self._relay_node = relay_node
        self._send_time_ms = None
        _button_pin = _cfg['pin'] # IO5
        self._button = PushButton(_button_pin, self._send_message)
        # post-topological initialization properties
        self._upstream_mac = self._relay_node.upstream_mac
        self._downstream_mac = self._relay_node.downstream_mac
        self._log.info('ready.')

    def receive_message(self, message):
        if self._send_time_ms is not None:
            rtt_ms = time.ticks_diff(time.ticks_ms(), self._send_time_ms)
            self._send_time_ms = None
            value = message.value
            self._log.info("round trip: {}ms elapsed on message:\n{}{}".format(rtt_ms, Fore.WHITE, message))
            self._log.info("inbound message: " + Fore.GREEN + "'{}'".format(value))

    def _send_message(self, arg=None):
        '''
        Triggered by the button press.
        '''
        # use sample value
        value = FoodNameGenerator.generate()
        self.send_message(value)

    def send_message(self, value=None):
        '''
        Initiates sending a message onto the relay.
        '''
        self._log.info("sending message '{}'…".format(value))
        if self._downstream_mac:
            self._send_time_ms = time.ticks_ms()
            self._log.info("outbound message: " + Fore.GREEN + "'{}'…".format(value))
            message = self._relay_node._message_factory.create_message(event=RELAY, value=value)
            # set callback to receive inbound message
            self._relay_node.set_receive_callback(self.receive_message)
            # send outbound (direction=1) down the chain
            self._relay_node.send_message(self._downstream_mac, 1, message)

#EOF
