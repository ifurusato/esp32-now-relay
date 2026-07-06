#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-26
# modified: 2026-06-26

import asyncio
import time
from collections import deque
from colorama import Fore, Style

from direction import *
from event import *
from message import Message
from publisher import Publisher
from subscriber import Subscriber
from logger import Logger, Level

class NetworkGateway(Publisher, Subscriber):
    NAME = 'gateway'
    '''
    A gateway between the network relay and the local message bus.
    '''
    def __init__(self, config=None, index=-1, message_bus=None, message_factory=None, relay=None, level=Level.INFO):
        Publisher.__init__(self, name=NetworkGateway.NAME, message_bus=message_bus, message_factory=message_factory, level=level, _init_base=False)
        Subscriber.__init__(self, name=NetworkGateway.NAME, message_bus=message_bus, enabled=True, level=level, _init_base=True)
        if config is None:
            raise TypeError('configuration argument is null.')
        _cfg = config['rros']['gateway']
        self._verbose = True # _cfg['verbose']
        self._index = index
        self._relay = relay
        self._is_initiator = self._index == 0
        self.add_events(Event.all())
        self._inbound_mac_bytes   = self._relay.inbound_mac_bytes
        self._outbound_mac_bytes = self._relay.outbound_mac_bytes
        self._queue = deque([], 10)
        # elapsed time trackers
        self._pending_trackers = {}
        self._max_capacity = 20
        self._log.info('ready.')

    # publisher  ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def publish(self, message):
        '''
        Publish a message to the bus if this publisher is active.
        '''
        if self.is_active:
            if self._verbose:
                self._log.info("publishing message: '{}'".format(message))
            self._message_bus.publish(message)
        else:
            self._log.warn('ignored: publisher not active.')

    # subscriber ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    async def process_message(self, message):
        '''
        Processes an incoming message, adding it to the queue (to avoid
        duplicate processing) and publishing it to the Relay if its tnid
        value is non-null.
        '''
        acknowledged = message.value.startswith('ack:')
        if message in self._queue:
            self._log.debug("ignoring already-published message: '{}'".format(message.id))
            return
        else:
            self._log.debug("processing message: " + Fore.GREEN + "'{}'…".format(message.id))
        if message.event is FAILURE:
            self._log.error("inbound message indicates error: " + Fore.RED + "'{}'".format(message.value))
        elif message.tnid is not None:
            if self._verbose:
                self._log.info("publishing message: "
                        + Fore.GREEN + "'{}'".format(message.value)
                        + Fore.CYAN + " with tnid '{}' to relay…".format(message.tnid))
            self._queue.append(message)
            direction = INBOUND if acknowledged else OUTBOUND
            self.publish_to_relay(direction, message)
        else:
            if self._verbose:
                self._log.debug("ignoring message: '{}' (no tnid)".format(message.id))

    def acceptable(self, message):
        '''
        Returns True for any event type, since we want to filter all events.
        '''
        return True

    # relay ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def _receive_message(self, message):
        '''
        The callback on inbound messages.
        '''
        _send_time = self._pending_trackers.pop(message.id, None)
        if _send_time is not None:
            _elapsed_ms = time.ticks_diff(time.ticks_ms(), _send_time)
            self._log.info("round trip: " 
                    + Fore.GREEN
                    + "{}ms ".format(_elapsed_ms) 
                    + Fore.CYAN
                    + "elapsed on message: " 
                    + Fore.GREEN
                    + "{} / {}".format(message.event.name, message.id)
                )
        else:
            self._log.warn("unable to determine round trip elapsed time; {} trackers.".format(len(self._pending_trackers)))
        # if initiator node, we remove tnid and push to local message bus
        if self._is_initiator:
            self._log.info("inbound message: " + Fore.GREEN + "'{}'".format(message.value) 
                    + Fore.CYAN + '; publishing to message bus…')
            message.tnid = None
            self._message_bus.publish(message)
        else:
            self._log.info("inbound message: " + Fore.GREEN + "'{}'".format(message.value)
                    + Fore.CYAN + Style.BRIGHT + '; stop.')

    def publish_to_relay(self, direction, message):
        '''
        Publishes the inbound or outbound message to the Relay.
        '''
        if not isinstance(direction, Direction):
            raise TypeError('expected direction argument.')
        if not isinstance(message, Message):
            raise TypeError('expected message argument.')
        value = message.value
        if self._verbose:
            self._log.info("sending message '{}'…".format(value))

        # outbound message tracking
        if len(self._pending_trackers) >= self._max_capacity:
            # pop oldest entry
#           self._log.debug("popping oldest entry from {} trackers…".format(len(self._pending_trackers)))
            self._pending_trackers.pop(next(iter(self._pending_trackers)))
        self._pending_trackers[message.id] = time.ticks_ms()
#       self._log.debug("adding message ID of type '{}' to trackers.".format(type(message.id), len(self._pending_trackers)))

        if direction is OUTBOUND and self._outbound_mac_bytes:
            if self._verbose:
                self._log.info("outbound message: " + Fore.GREEN + "'{}'".format(value))
            # set callback to receive inbound message
            self._relay.set_receive_callback(self._receive_message)
            # send outbound down the chain
            self._relay.send_message(self._outbound_mac_bytes, OUTBOUND, message)
        elif direction is INBOUND and self._inbound_mac_bytes:
            if self._verbose:
                self._log.info("B. inbound message: " + Fore.GREEN + "'{}'".format(value))
            # send inbound up the chain
            self._relay.send_message(self._inbound_mac_bytes, INBOUND, message)
        else:
            self._log.error("unable to send message {}: ".format(direction.name) + Fore.RED + "'{}'".format(value))

#EOF
