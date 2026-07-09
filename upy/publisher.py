#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2019-12-23
# modified: 2026-07-03

from component import Component
from logger import Level

class Publisher(Component):
    '''
    A base publisher that pushes messages onto the message bus.

    :param name:             the publisher name
    :param message_bus:      the message bus
    :param message_factory:  the message factory
    :param suppressed:       if True, initially suppress
    :param enabled:          if True, initially enable
    :param _init_base:       if False, do not initialise the base class (default True)
    :param level:            the logging level
    '''
    def __init__(self,
            name=None,
            message_bus=None,
            message_factory=None,
            suppressed=False,
            enabled=False,
            _init_base=True,
            level=Level.INFO):
        if _init_base:
            Component.__init__(
                self,
                name='pub:{}'.format(name),
                suppressed=suppressed,
                enabled=enabled,
                level=level
            )
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
        elif not self.enabled and not self.suppressed:
            self._log.warn('ignored: publisher not active (disabled).')
        elif self.suppressed and self.enabled:
            self._log.warn('ignored: publisher not active (suppressed).')
        else:
            self._log.warn('ignored: publisher not active.')

#EOF
