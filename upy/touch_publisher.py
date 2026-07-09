#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-07-05
# modified: 2026-07-05
#
# ESP-NOW RELAY

import asyncio
import time
from machine import I2C
from colorama import Fore, Style

import mpr121
from publisher import Publisher
from event import TOUCH
from logger import Logger, Level
from explorer_button import ExplorerButton

class TouchPublisher(Publisher):
    NAME = 'touch'
    '''
    A publisher subclass that polls the MPR121 touch sensor on the
    Unexpected Maker TinyPICO Explorer Shield within an asyncio task
    and publishes touch events.
    '''
    def __init__(self, config=None, message_bus=None, message_factory=None, level=Level.INFO):
        Publisher.__init__(self,
                name=TouchPublisher.NAME,
                message_bus=message_bus,
                message_factory=message_factory,
                suppressed=False, enabled=False, level=level)
        _cfg = config['rros']['touch_publisher']
        self._verbose    = _cfg['verbose']
        self._active     = _cfg['active']
        poll_interval_ms = _cfg['poll_interval_ms']
        self._debounce_delay_ms = _cfg.get('debounce_delay_ms', 333)
        # I2C
        scl_pin = 22
        sda_pin = 21
        self._i2c = I2C(1, scl=scl_pin, sda=sda_pin, freq=400000)
        self._mpr = mpr121.MPR121(self._i2c)
        self._poll_interval_ms = poll_interval_ms

        # State tracking using the unified instances
        self._button_states = {btn: 0 for btn in ExplorerButton.all()}

        # Tracks the last ticks_ms timestamp when a message was published for each button
        self._last_publish_time = {btn: 0 for btn in ExplorerButton.all()}

        self._task = None
        self._log.info('ready.')

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def enable(self):
        '''
        Starts the asynchronous loop task for polling the touch sensor.
        '''
        if not self.enabled:
            if self._task is None:
                self._task = asyncio.create_task(self._run())
            super().enable()
            self._log.info('enabled.')
        else:
            self._log.warn('already enabled.')

    def disable(self):
        '''
        Cancels the asynchronous polling task.
        '''
        if not self.disabled:
            if self._task is not None:
                self._task.cancel()
                self._task = None
            super().disable()
            self._log.warn('disabled.')
        else:
            self._log.warn('already disabled.')

    def _check_buttons(self):
        k = self._mpr.touched()
        btn = ExplorerButton.by_mask(k)
        if btn is not None:
            self._button_states[btn] = 1
        return btn

    async def _run(self):
        '''
        The continuous non-blocking polling loop executed by asyncio.
        '''
        while self.enabled:
            try:
                if self.is_active:
                    btn = self._check_buttons()
                    if btn is not None:
                        now = time.ticks_ms()
                        # Calculate time elapsed since this specific button last successfully published
                        if time.ticks_diff(now, self._last_publish_time[btn]) >= self._debounce_delay_ms:
                            self._last_publish_time[btn] = now

                            message = self._message_factory.create_message(TOUCH, btn.name)
                            message.tnid = '*'
                            if self._active:
                                self.publish(message)
                            if self._verbose:
                                self._log.info(Fore.WHITE + 'published: {}'.format(message))

                await asyncio.sleep_ms(self._poll_interval_ms)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log.error(
                    "Error in MPR121 poll loop: {}".format(str(e))
                )
                await asyncio.sleep_ms(self._poll_interval_ms)

#EOF
