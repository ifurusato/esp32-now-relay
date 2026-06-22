#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2020-11-10
# modified: 2026-06-04

import asyncio
from logger import Logger, Level

class MessageBus:
    '''
    A simplified asynchronous message bus. Messages are published synchronously
    to a list-backed FIFO queue and consumed asynchronously, delivering each
    message to all enabled, accepting subscribers.

    :param level: the logging level
    '''
    def __init__(self, level=Level.INFO):
        self._log         = Logger('bus', level)
        self._queue       = []
        self._subscribers = []
        self._enabled     = False
        self._log.info('ready.')

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def add_subscriber(self, subscriber):
        self._subscribers.append(subscriber)
        self._log.info('added subscriber: {}'.format(subscriber.name))

    def remove_subscriber(self, subscriber):
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    @property
    def subscribers(self):
        return self._subscribers

    def publish(self, message):
        '''
        Synchronously add a message to the FIFO queue.
        '''
        self._log.info('publish: {}'.format(message))
        self._queue.append(message)

    def queue_size(self):
        return len(self._queue)

    def queue_empty(self):
        return len(self._queue) == 0

    def enable(self):
        self._enabled = True
        self._log.info('enabled.')

    def disable(self):
        self._enabled = False
        self._log.info('disabled.')

    def close(self):
        self._enabled = False

    async def consume_loop(self):
        '''
        Async consume loop: dequeues messages and delivers to all enabled,
        accepting subscribers. Start as a task from within an async context.
        '''
        self._log.info('consume loop started.')
        while self._enabled:
            if self._queue:
                _message = self._queue.pop(0)
                for _subscriber in self._subscribers:
                    if _subscriber.is_active and _subscriber.acceptable(_message):
                        await _subscriber.process_message(_message)
            else:
                await asyncio.sleep_ms(10)
        self._log.info('consume loop ended.')

#EOF
