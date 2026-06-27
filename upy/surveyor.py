#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-26
# modified: 2026-06-28

import asyncio
import time
from collections import deque
from colorama import Fore, Style

from colors import *
from event import *
from publisher import Publisher
from subscriber import Subscriber
from logger import Logger, Level

class Surveyor(Publisher, Subscriber):
    NAME = 'surveyor'
    '''
    Subscribes to SURVEY messages, decorates them and republishes them.
    '''
    def __init__(self, config=None, index=-1, networking=None, message_bus=None, message_factory=None, level=Level.INFO):
        Publisher.__init__(self, name=Surveyor.NAME, message_bus=message_bus, message_factory=message_factory, level=level, _init_base=False)
        Subscriber.__init__(self, name=Surveyor.NAME, message_bus=message_bus, enabled=True, level=level, _init_base=True)
        if config is None:
            raise TypeError('configuration argument is null.')
        _cfg = config['rros']['surveyor']
        self._verbose = _cfg['verbose']
        self._index = index
        self._is_initiator = index == 0
        self._networking = networking
        self._is_v2_compatible = None
        self.add_event(SURVEY)
        self._queue = deque([], 10)
        self._callback = None
        self._log.info('ready.')

    @property
    def index(self):
        return self._index

    @property
    def is_v2_compatible(self):
        '''
        After the survey has completed
        '''
        if self._is_v2_compatible is None:
            raise RuntimeError('no value available: survey has not completed.')
        return self._is_v2_compatible

    def _append_node_info(self, message):
        '''
        Modifies the existing message value by appending a node identifier
        followed by the ESP-NOW version for this node.
        '''
        _node_id = str(self._index + 1)
        _version = self._networking.espnow_version
        _value = '{}n{}-{};'.format(message.value, _node_id, _version)
#       self._log.debug("setting message value to: '{}'".format(_value))
        message.value = _value

    def send(self, callback=None):
        '''
        Initiates a survey message, publishing a new Message to the MessageBus.
        '''
        self._log.info('initiating survey…')
        _message = self._message_factory.create_message(SURVEY, 'survey:')
        _message.tnid = '*'
        if callback:
            self._callback = callback
        return self.publish(_message)

    def _complete_survey(self, message):
        result = self._parse_survey(message.value)
        _is_v2_compatible = True
        if result:
            self._log.info('ESP-NOW version survey:')
            for id, value in sorted(result.items()):
                if value == 1:
                    _is_v2_compatible = False  
                self._log.info("  node {}: ".format(id) + Fore.GREEN + "V{}".format(value))
            self._is_v2_compatible = _is_v2_compatible
            if self._is_v2_compatible:
                self._log.info('using ESP-NOW V2.0: compatible across all nodes.')
                self._networking.set_espnow_v2_compatible()
            else:
                self._log.warn('using ESP-NOW V1.0: not compatible with V2.0 across all nodes.')
            if self._callback:
                self._callback(COLOR_DEEP_CYAN)
        else:
            self._log.warn('survey returned invalid results.')
            if self._callback:
                self._callback(COLOR_RED)

    def _parse_survey(self, value):
        if not value.startswith("ack:"):
            return None
        value = value[4:]
        if not value.startswith("survey:"):
            return None
        value = value[7:]
        result = {}
        for item in value[:-1].split(";"):
            node, value = item.split("-")
            result[node] = int(value)
        return result

    def publish(self, message):
        '''
        Publish a message to the bus if this publisher is active.
        '''
        return super().publish(message)

    async def process_message(self, message):
        '''
        Processes an incoming Message (as a Subscriber), then republishes the
        message after altering its message value.
        '''
        if message in self._queue:
#           self._log.debug("ignoring already-published message: '{}'".format(message.id))
            return
        if self._is_initiator and message.value.startswith("ack:"):
            self._complete_survey(message)
            return
        self._append_node_info(message)
        self._queue.append(message) # add modified message to queue to avoid multiple publications
        if self._verbose:
            self._log.info("publishing message: "
                    + Fore.GREEN + "'{}'".format(message.value)
                    + Fore.CYAN + " with tnid '{}' to relay…".format(message.tnid))
        self.publish(message)

#EOF
