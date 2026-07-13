#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-07-06
# modified: 2026-07-13
#
# ESP-NOW RELAY

from machine import RTC as _RTC
from colorama import Fore, Style

from logger import Logger, Level
from event import RTC
from subscriber import Subscriber

class RtcSubscriber(Subscriber):
    NAME = 'rtc'
    '''
    A subscriber that receives RTC event messages and sets the node's
    date and time accordingly.

    Note that this subscriber should not be active on the initiator node.
    '''
    def __init__(self, config, message_bus, level=Level.INFO):
        Subscriber.__init__(self, RtcSubscriber.NAME, suppressed=False, enabled=True, message_bus=message_bus, level=level)
        _cfg = config['rros']['rtc_subscriber']
        self._verbose = _cfg['verbose']
        self.add_event(RTC)
        self._rtc = _RTC()
        self._log.info('ready.')

    async def process_message(self, message):
        '''
        Decodes the message payload back into an ExplorerButton instance.
        '''
        if self.enabled:
            if self._verbose:
                self._log.info('process message: ' + Fore.GREEN + '{}'.format(message))
            datetime = tuple(int(x) for x in message.value.split(","))
            self._rtc.datetime(datetime)
            self._log.info('set RTC datetime to: ' + Fore.WHITE + Style.BRIGHT + '{}'.format(self.format_datetime(datetime)))
        else:
            self._log.warn('cannot process message: disabled.')

    def format_datetime(self, dt):
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(dt[0], dt[1], dt[2], dt[4], dt[5], dt[6])

    def disable(self):
        if self.enabled:
            super().disable()
            self.clear_events()
            self._rtc = None
            self._log.debug('disabled.')
        else:
            self._log.warn('already disabled.')

    def close(self):
        if not self.closed:
            super().close()
            self._log.debug('closed.')
        else:
            self._log.warn('already closed.')

#EOF
