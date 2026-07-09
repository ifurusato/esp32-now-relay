#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2020-11-10
# modified: 2026-07-07

import asyncio
from colorama import Fore, Style

from logger import Logger, Level
from component import Component

class MessageBus(Component):
    NAME = 'msg-bus'
    _instance = None
    '''
    A singleton asynchronous publish-and-subscribe message bus. Messages
    are published synchronously to a list-backed FIFO queue and consumed
    asynchronously, delivering each message to all enabled, accepting
    subscribers.

    :param level: the logging level
    '''
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MessageBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, level=Level.INFO):
        if self._initialized:
            return
        self._initialized = True
        Component.__init__(self, MessageBus.NAME, suppressed=False, enabled=False)
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
#       self._log.debug('publish message: ' + Fore.GREEN + '{}'.format(message))
        self._queue.append(message)

    def queue_size(self):
        return len(self._queue)

    def queue_empty(self):
        return not self._queue

    def clear_queue(self):
        self._queue.clear()

    def close(self):
        super().close()

    def enable(self):
        '''
        Enable the message bus and start the processing loop.
        This call will block until disable() is called.
        '''
        if not self.closed and not self.enabled:
            super().enable()
#           self._log.debug('starting message bus loop…')
            try:
                asyncio.run(self._start_consuming())
            except KeyboardInterrupt:
                self._log.info('interrupted via keyboard.')
            finally:
                self.disable()
        else:
            self._log.warn('already enabled or closed.')

    async def _start_consuming(self):
        '''
        Async consume loop: dequeues messages and delivers to all enabled,
        accepting subscribers.
        '''
        self._log.info(Fore.GREEN + 'message bus loop started.')
        while self.enabled:
            if self._queue:
                _message = self._queue.pop(0)
#               self._log.debug('consuming message ID: {}; TNID: {}; for {} subscribers.'.format(_message.id, _message.tnid, len(self._subscribers)))
                for _subscriber in self._subscribers:
#                   self._log.debug('subscriber: {}; active? {}'.format(_subscriber, _subscriber.is_active))
                    if _subscriber.is_active and _subscriber.acceptable(_message):
                        await _subscriber.process_message(_message)
            else:
                await asyncio.sleep_ms(10)
        self._log.info('message bus loop ended.')

    def disable(self):
        '''
        Disable the message bus, clearing the queue and shutting down loops.
        '''
        if not self.enabled:
            self._log.warn('already disabled.')
        else:
            self._log.info('disabling…')
            self.clear_queue()
            super().disable()

    def close(self):
        self._closed = True
        self.disable()

#EOF
