#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2021-03-10
# modified: 2026-06-23

import time
from uuid import UUID, uuid4

class Message:
    '''
    A message carrying an Event and an optional value, timestamped at creation
    using ticks_ms.

    Do not create directly: use Publisher.publish() or construct via the bus.

    :param event:  the Event associated with this message
    :param value:  the optional value payload
    '''
    def __init__(self, event, value=None):
        if event is None:
            raise ValueError('null event argument.')
        self._id        = uuid4()
        self._event     = event
        self._value     = value
        self._timestamp = time.ticks_ms()

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

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

    @timestamp.setter
    def timestamp(self, timestamp):
        self._timestamp = timestamp

    @property
    def age_ms(self):
        return time.ticks_diff(time.ticks_ms(), self._timestamp)

    def __repr__(self):
        return 'Message[\n  id={},\n  event={},\n  value={},\n  age={}ms\n]'.format(
                self._id, self._event.label, self.value, self.age_ms)

#EOF
