#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2019-12-23
# modified: 2026-06-28

from component import Component
from logger import Level

class Publisher(Component):
    '''
    A base publisher that pushes messages onto the message bus.

    :param name:         the publisher name
    :param message_bus:  the message bus
    :param level:        the logging level
    '''
    def __init__(self, name, message_bus, message_factory, suppressed=False, enabled=False, _init_base=True, level=Level.INFO):
#       super().__init__('pub:{}'.format(name), suppressed=suppressed, enabled=enabled, level=level)
        if _init_base:
            Component.__init__(
                self,
                name='pub:{}'.format(name),
                suppressed=suppressed,
                enabled=enabled,
                level=level
            )
        if message_bus is None:
            raise TypeError('message bus argument was null.')
        if message_factory is None:
            raise TypeError('message factory argument was null.')
        self._message_bus = message_bus
        self._message_factory = message_factory

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @property
    def message_bus(self):
        return self._message_bus

    def publish(self, message):
        '''
        Publish a message to the bus if this publisher is active.
        '''
        if self.is_active:
            self._message_bus.publish(message)
            return True
        else:
            self._log.warn('ignored: publisher not active.')
            return False

#EOF
