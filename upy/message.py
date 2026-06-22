#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2021-03-10
# modified: 2026-06-04

import time

_counter = 0

class Message:
    '''
    A message carrying an Event and an optional value, timestamped at creation
    using ticks_ms.

    Do not create directly: use Publisher.publish() or construct via the bus.

    :param event:  the Event associated with this message
    :param value:  the optional value payload
    '''
    def __init__(self, event, value=None):
        global _counter
        if event is None:
            raise ValueError('null event argument.')
        self._event     = event
        self._value     = value
        self._timestamp = time.ticks_ms()
        self._id        = _counter
        _counter       += 1

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @property
    def id(self):
        return self._id

    @property
    def event(self):
        return self._event

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def age_ms(self):
        return time.ticks_diff(time.ticks_ms(), self._timestamp)

    def __repr__(self):
        return 'Message[id={}, event={}, age={}ms]'.format(
                self._id, self._event.label, self.age_ms)

#EOF
