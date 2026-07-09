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
#
# ESP-NOW RELAY

import asyncio
import sys
import time
from collections import deque
from colorama import Fore, Style

from logger import Logger, Level
from colors import *
from event import *
from publisher import Publisher
from subscriber import Subscriber
from message_factory import MessageFactory

class Surveyor(Publisher, Subscriber):
    NAME = 'surveyor'
    SURVEY_PFX = 'survey:'
    V1_SIGNAL  = 'survey:v1.0'
    V2_SIGNAL  = 'survey:v2.0'
    '''
    Subscribes to SURVEY messages, decorates them and republishes them.

    The survey is of the ESP-NOW version of each node. The survey is started
    on the Initiator (node 1) and sent across the relay, returning with the
    results of each node's ESP-NOW version. If all nodes are ESP-NOW V2.0,
    a second survey message is sent out with a payload of "survey:v2.0", to
    set each node's MessageFactory accordingly.
    '''
    def __init__(self, config=None, networking=None, message_bus=None, message_factory=None, relay=None, level=Level.INFO):
        Publisher.__init__(self, name=Surveyor.NAME, message_bus=message_bus, message_factory=message_factory, level=level, _init_base=False)
        Subscriber.__init__(self, name=Surveyor.NAME, message_bus=message_bus, enabled=True, level=level, _init_base=True)
        if config is None:
            raise TypeError('configuration argument is null.')
        _cfg = config['rros']['surveyor']
        self._verbose      = _cfg['verbose']
        self._is_initiator = relay.is_initiator()
        self._is_endpoint  = relay.is_endpoint()
        self._index        = relay.index
        self._networking   = networking
        self._is_v2_compatible = None
        self.add_event(SURVEY)
        self._queue = deque([], 10)
        self._callback     = None
        self._completed    = False
        self._log.info('ready.')

    def set_is_endpoint(self):
        '''
        If this is the endpoint node, the relay calls this to set the flag True.
        '''
        self._is_endpoint = True

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

    def _set_espnow_v2(self):
        self._log.info(Fore.MAGENTA + 'setting ESP-NOW version to V2.0.')
        MessageFactory.set_espnow_version(2)

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
        _message = self._message_factory.create_message(SURVEY, Surveyor.SURVEY_PFX)
        _message.tnid = '*'
        if callback:
            self._callback = callback
        return self.publish(_message)

    def _complete_survey(self, message):
        self._log.info('survey complete.')
        try:
            if message.event == FAILURE:
                self._log.error('survey failure.')
                self._completed = True
                return
            # returns the node survey or a boolean
            result = self._parse_survey(message.value)
            _is_v2_compatible = True
            if result is not None:
                if isinstance(result, bool):
                    self._log.info('parsed survey version; returned.')
                    self._is_v2_compatible = result
                else:
                    self._log.info('ESP-NOW version survey:')
                    for id, value in sorted(result.items()):
                        if value == 1:
                            _is_v2_compatible = False  
                            self._log.info("  node {}: ".format(id) + Fore.GREEN + "V{}".format(value))
                        else:
                            self._log.info("  node {}: ".format(id) + Fore.GREEN + Style.BRIGHT + "V{}".format(value))
                    self._is_v2_compatible = _is_v2_compatible

                if self._is_v2_compatible:
                    self._log.info('using ESP-NOW V2.0: compatible across all nodes.')
                    self._networking.set_espnow_v2_compatible()
                    MessageFactory.set_espnow_version(2)
                else:
                    self._log.warn('using ESP-NOW V1.0: not compatible with V2.0 across all nodes.')
                    MessageFactory.set_espnow_version(1)
                if self._callback:
                    self._callback(COLOR_DEEP_CYAN)
            else:
                self._log.warn('survey returned invalid results.')
                if self._callback:
                    self._callback(COLOR_RED)
            if self._is_initiator:
                if _is_v2_compatible:
                    self._log.info(Fore.MAGENTA + 'confirmed as V2.0 capable.')
#                   _message = self._message_factory.create_message(SURVEY, Surveyor.V2_SIGNAL)
#                   self._log.info(Fore.MAGENTA + 'sending V2.0 confirmation message ({}) to other nodes…'.format(_message.id))
#                   _message.tnid = '*'
#                   self._queue.append(_message)
#                   self.publish(_message)
            elif self._is_endpoint:
                _message.tnid = None
        finally:
            self._completed = True

    def _parse_survey(self, value):
        '''
        Returns a dict of the survey results unless the value is
        already a V1.0 or v2.0 signal, in which it returns a boolean.
        '''
        _orig_value = value
        if not value.startswith("ack:"):
            return None
        value = value[4:]
        if not value.startswith("survey:"):
            return None
        if value == Surveyor.V1_SIGNAL:
            self._log.info('🤢 _parse_survey: False')
            return False
        elif value == Surveyor.V2_SIGNAL:
            self._log.info('🤢 _parse_survey: True')
            return True
        try:
            value = value[7:]
            result = {}
            for item in value[:-1].split(";"):
                node, value = item.split("-")
                result[node] = int(value)
            return result
        except Exception as e:
            self._log.error("{} thrown parsing survey results '{}': {}".format(type(e), _orig_value, e))
            sys.print_exception(e)
            return None

    def publish(self, message):
        '''
        Publish a message to the bus if this publisher is active.
        '''
        if self._completed:
            self._log.warn("cannot publish: survey already completed.")
            return False
        else:
            return super().publish(message)

    async def process_message(self, message):
        '''
        Processes an incoming Message (as a Subscriber), then republishes the
        message after altering its message value.
        '''
        if self._completed:
            self._log.info('🤢 process_message: is already completed.')
            self._log.warn("message ignored: survey already completed.")
            return
        elif message in self._queue:
            self._log.info(Fore.BLACK + "ignoring already-published message: '{}'".format(message.id))
            return
        if self._is_initiator and message.value.startswith("ack:"):
            self._log.info(Fore.BLACK + 'acknowledging inbound message: {}'.format(message.id))
            self._complete_survey(message)
            return
        if message.value == Surveyor.V2_SIGNAL:
            self._log.info('🤢 process_message: received V2.0 signal.')
            self._set_espnow_v2()
        else:
            self._append_node_info(message)
        self._queue.append(message) # add modified message to queue to avoid multiple publications
        if self._verbose:
            self._log.info("publishing message: "
                    + Fore.GREEN + "'{}'".format(message.value)
                    + Fore.CYAN + " with tnid '{}' to relay…".format(message.tnid))
        self.publish(message)

#EOF
