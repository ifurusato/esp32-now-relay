#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2021-03-10
# modified: 2026-07-03

import time
from colorama import Fore, Style

from event import Event
from util import Util

class Message:
    '''
    A message carrying an Event and an optional value, timestamped at creation
    using ticks_ms.

    If the 'tnid' (target node ID) value has been set, this indicates that the
    Message recipients are other nodes on the Relay.

    There are no type restrictions on the value.

    Do not create directly: use the MessageFactory.

    :param id:     the unique message identifier (a UUID)
    :param event:  the Event associated with this message
    :param value:  the optional value payload
    '''
    def __init__(self, id, event, value=None):
        if id is None:
            raise ValueError('null id argument.')
        if event is None:
            raise ValueError('null event argument.')
        self._id        = id
        if not isinstance(event, Event):
            raise TypeError('expected an event, not {}'.format(type(event)))
        self._event     = event
        self._value     = value
        self._tnid      = None # target node ID
        self._timestamp = time.ticks_ms()

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        '''
        To be used only during deserialisation.
        '''
        self._id = value

    @property
    def tnid(self):
        return self._tnid

    @tnid.setter
    def tnid(self, value):
        '''
        The 'tnid' (target node ID) value can contain a single node identifier,
        a list of whitespace-delimited node identifiers, or '*' to indicate all.
        If None this indicates the message is not meant for network transit.
        '''
        self._tnid = value

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, value):
        self._event = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._timestamp = timestamp

    @property
    def age_ms(self):
        return time.ticks_diff(time.ticks_ms(), self._timestamp)

    def copy(self):
        '''
        Returns a shallow copy of the Message instance, preserving all internal state.
        '''
        msg = Message(self._id, self._event, self._value)
        msg._tnid = self._tnid
        msg._timestamp = self._timestamp
        return msg

    def __eq__(self, other):
        if not isinstance(other, Message):
            return False
        return (
            self._id == other._id
            and self._event == other._event
            and self._value == other._value
            and self._tnid == other._tnid
            and self._timestamp == other._timestamp
        )

    @staticmethod
    def _format_value(value, max_len=30):
        '''
        Convert non-string types (like tuples, lists, ints) to a safe string representation.
        '''
        if value is None:
            return "None"
        has_magenta = Fore.MAGENTA in value
        val_str = str(value) if not isinstance(value, str) else value
        return Util.ellipsis(val_str, max_len)

    def __repr__(self):
        return 'Message[\n  id={},{}\n  event={},\n  value={},\n  timestamp={}ms\n]'.format(
                self._id,
                ('\n  tnid={}'.format(self._tnid) if self._tnid else ''),
                self._event.name,
                Message._format_value(self._value, 50),
                self.timestamp
            )

#EOF
