#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-26
# modified: 2026-07-07
#
# ESP-NOW RELAY

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
    def __init__(self, config=None, message_bus=None, message_factory=None, relay=None, level=Level.INFO):
        Publisher.__init__(self, name=NetworkGateway.NAME, message_bus=message_bus, message_factory=message_factory, level=level, _init_base=False)
        Subscriber.__init__(self, name=NetworkGateway.NAME, message_bus=message_bus, enabled=True, level=level, _init_base=True)
        if config is None:
            raise TypeError('configuration argument is null.')
        _cfg = config['rros']['gateway']
        self._verbose = _cfg['verbose']
        self._relay = relay
        self._relay.set_gateway(self)
        self._is_initiator = relay.is_initiator()
        self._is_endpoint  = relay.is_endpoint()
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
                self._log.info('publishing message: ' + Fore.GREEN + '{}'.format(message))
            self._message_bus.publish(message)
        else:
            self._log.warn('ignored: publisher not active.')

    # subscriber ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def receive_from_relay(self, message):
        '''
        Receives a message from the Relay, publishing to the MessageBus.
        '''
        if self._verbose:
            self._log.info("receiving message from relay: " + Fore.GREEN + "'{}'…".format(message.id))
        self.publish(message)

    async def process_message(self, message):
        '''
        Processes an incoming message, adding it to the queue (to avoid
        duplicate processing) and publishing it to the Relay if its tnid
        value is non-null.

        If this is the endpoint it is at this point considered acknowledged (after
        all local processing has occurred) so "ack:" is prepended to the message
        value before it is published back to the Relay.
        '''
        if message in self._queue:
            self._log.debug("ignoring already-published message: '{}'".format(message.id))
            return
        elif self._verbose:
            self._log.debug("processing message: " + Fore.GREEN + "'{}'…".format(message.id))
        if message.event is FAILURE:
            self._log.error("inbound message indicates error: " + Fore.RED + "'{}'".format(message.value))
        elif message.tnid is not None:
            if self._verbose:
                self._log.info("publishing message: "
                        + Fore.GREEN + "'{}'".format(message.value)
                        + Fore.CYAN + " with tnid '{}' to relay…".format(message.tnid))
            self._queue.append(message)
            if self._is_endpoint:
                message = self._process_endpoint_logic(message)
                if self._verbose:
                    self._log.info('processed endpoint message: ' + Fore.GREEN + '{}'.format(message))
            acknowledged = message.value.startswith('ack:')
            direction = INBOUND if acknowledged else OUTBOUND
            self.publish_to_relay(direction, message)
        else:
            if self._verbose:
                self._log.debug("ignoring message: '{}' (no tnid)".format(message.id))

    def _process_endpoint_logic(self, message):
        '''
        Creates a clone of the original message, prepends "ack:" to the message value,
        then returns the clone. We don't want to modify the original message as it may
        still be being processed somewhere within the node.
        '''
        copy = message.copy()
        # prepend 'ack:' to string
        response_value = "ack:{}".format(message.value)
        copy.value = response_value
        if self._verbose:
            self._log.info('processed endpoint logic for message: ' + Fore.GREEN + '{}'.format(copy))
        return copy

    # relay ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def _receive_message(self, message):
        '''
        The callback on inbound messages.
        This removes the tnid value if this is the initiator node, to avoid
        infinite cycles.
        '''
        if self._verbose:
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
            if self._verbose:
                self._log.info("inbound message: " + Fore.GREEN + "'{}'".format(message.value) 
                        + Fore.CYAN + '; publishing to message bus…')
            message.tnid = None
            self._message_bus.publish(message)
        elif self._verbose:
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
#       self._log.debug("adding message ID of type '{}' to trackers.".format(type(message.id), len(self._pending_trackers)))
        self._pending_trackers[message.id] = time.ticks_ms()

        if direction is OUTBOUND:
            if self._is_endpoint:
                self._log.error("at endpoint: cannot send outbound message: " + Fore.GREEN + '{}'.format(message))
            elif self._outbound_mac_bytes:
                if self._verbose:
                    self._log.info("outbound message: " + Fore.GREEN + "'{}'".format(value))
                # set callback to receive inbound message
                self._relay.set_receive_callback(self._receive_message)
                # send outbound down the chain
                self._relay.send_message(self._outbound_mac_bytes, OUTBOUND, message)
            else:
                self._log.error("no peer available to send outbound message: " + Fore.RED + '{}'.format(message))
        elif direction is INBOUND:
            if self._is_initiator:
                self._log.error("at initiator: cannot send inbound message: " + Fore.GREEN + '{}'.format(message))
            elif self._inbound_mac_bytes:
                if self._verbose:
                    self._log.info("inbound message: " + Fore.GREEN + "'{}'".format(value))
                # send inbound up the chain
                self._relay.send_message(self._inbound_mac_bytes, INBOUND, message)
            else:
                self._log.error("no peer to send inbound message: " + Fore.RED + '{}'.format(message))
        else:
            self._log.error("unable to send message: " + Fore.RED + '{}'.format(message))

#EOF
