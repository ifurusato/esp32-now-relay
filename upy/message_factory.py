#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2019-12-23
# modified: 2026-06-18

from colorama import Fore, Style

from component import Component
from logger import Logger, Level
from message import Message
from message_bus import MessageBus
from event import Event

class MessageFactory(Component):
    '''
    A factory for Messages.
    '''
    def __init__(self, message_bus=None, level=Level.INFO):
#       self._log = Logger("msg-factory", level)
        Component.__init__(self, "msg-factory", suppressed=False, enabled=True, level=level)
        if message_bus is None:
            raise ValueError('null message bus argument.')
        elif not isinstance(message_bus, MessageBus):
            raise ValueError('wrong type for message bus: {}'.format(type(message_bus)))
        self._message_bus = message_bus
        self._log.info('ready.')

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def create_message(self, event=None, value=None):
        '''
        Create and return a new message with the supplied event and optional
        value. Not all event types are associated with a value.
        '''
        _message = Message(event=event, value=value)
        return _message

#EOF
