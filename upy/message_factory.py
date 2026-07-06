#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2019-12-23
# modified: 2026-06-26

from colorama import Fore, Style
from uuid import UUID, uuid4

from component import Component
from logger import Logger, Level
from message import Message
from message_bus import MessageBus
from event import Event
from message_codec import MessageCodec

class MessageFactory(Component):
    #  Packet limit lengths are respectively 250 for V1.0 and 1470 bytes for V2.0.
    MAX_DATA_LEN_V1  = 250 
    MAX_DATA_LEN_V2  = 1470
    OVERHEAD         = 100
    # maximum length of value given typical payload size and ESP32-NOW V1.0's 250 byte limit
    MAX_VALUE_LENGTH =  MAX_DATA_LEN_V1 - OVERHEAD
    ESP_NOW_VERSION  = 1

    _instance = None
    '''
    A factory for Messages.
    '''
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MessageFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, message_bus=None, level=Level.INFO):
        if self._initialized:
            return
        self._initialized = True

        Component.__init__(self, "msg-factory", suppressed=False, enabled=True, level=level)
        if message_bus is None:
            raise ValueError('null message bus argument.')
        elif not isinstance(message_bus, MessageBus):
            raise ValueError('wrong type for message bus: {}'.format(type(message_bus)))
        self._message_bus = message_bus
        self._log.info('ready.')

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @property
    def espnow_version(self):
        return MessageFactory.ESP_NOW_VERSION

    @staticmethod
    def set_espnow_version(version):
        '''
        This updates the maximum length of a message value to correspond with what
        can be supported by the ESP-NOW protocol minus the transport overhead. For
        V1.0 is (250 - 100 = 150 chars); for V2.0 is (1470 - 100 = 1370 chars).
        '''
        if version == 1:
            MessageFactory.MAX_VALUE_LENGTH = MessageFactory.MAX_DATA_LEN_V1 - MessageFactory.OVERHEAD
            MessageFactory.ESP_NOW_VERSION  = 1
        elif version == 2:
            MessageFactory.MAX_VALUE_LENGTH = MessageFactory.MAX_DATA_LEN_V2 - MessageFactory.OVERHEAD
            MessageFactory.ESP_NOW_VERSION  = 2

    def create_message(self, event=None, value=None):
        '''
        Create and return a new message with the supplied event and optional
        value. Not all event types are associated with a value.
        '''
        if isinstance(value, str) and MessageCodec.DELIMITER in value:
            raise ValueError("message value cannot contain the protocol delimiter '{}'".format(MessageCodec.DELIMITER))
        if len(value) > MessageFactory.MAX_VALUE_LENGTH:
                raise ValueError("message value exceeds maximum allowable length of {:d} characters".format(MessageFactory.MAX_VALUE_LENGTH))
        _uuid = str(uuid4())
        _message = Message(id=_uuid, event=event, value=value)
        return _message

#EOF
