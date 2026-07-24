#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-07-21
# modified: 2026-07-21

import asyncio
import machine
import time
from colorama import Fore, Style

from colors import *
from event import TOUCH
from touch_pad import TouchPad
from logger import Logger, Level
from publisher import Publisher

class TouchPadPublisher(Publisher):
    NAME = 'touch'
    '''
    Provides support for all the TouchPad instances of the RobotPad controller.
    '''
    def __init__(self, config=None, message_bus=None, message_factory=None, pixel=None, level=Level.INFO):
        Publisher.__init__(self,
                name=TouchPadPublisher.NAME,
                message_bus=message_bus,
                message_factory=message_factory,
                suppressed=False,
                enabled=False,
                level=level)
        self._pixel = pixel
        self._message_bus = message_bus
        self._message_factory = message_factory
        _cfg = config['rros']['touch_pad_publisher']
        self._threshold  = _cfg['threshold']
        self._poll_ms    = _cfg['poll_ms']
        self._on_touch   = _cfg['on_touch']
        self._on_release = _cfg['on_release']
        self._enable_led = _cfg['enable_led']
        self._led_duration_ms   = _cfg['led_duration_ms']
        self._debounce_delay_ms = _cfg['debounce_delay_ms']
        self._last_publish_time = {}
        self._touch      = {}
        self._is_touched = {}
        self._task       = None
        self._led_task   = None
        for pad in TouchPad.all():
            self._touch[pad] = machine.TouchPad(machine.Pin(pad.pin))
            self._is_touched[pad] = False
            self._last_publish_time[pad] = 0
        self._log.info('ready.')

    def enable(self):
        '''
        Starts the asynchronous loop task for polling the touch sensor.
        '''
        if not self.enabled:
            if self._task is None:
                self._task = asyncio.create_task(self._start())
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

    @property
    def touch_pads(self):
        return TouchPad.all()

    async def _start(self):
        self._task = asyncio.create_task(self._poll_loop())

    async def _poll_loop(self):
        '''
        The continuous non-blocking polling loop executed by asyncio.
        '''
        while self.enabled:
            try:
                for pad in TouchPad.all():
                    value = self._touch[pad].read()
                    touched = value > self._threshold
                    if touched != self._is_touched[pad]:
                        self._is_touched[pad] = touched
                        if touched and self._on_touch:
                            now = time.ticks_ms()
                            if time.ticks_diff(now, self._last_publish_time[pad]) >= self._debounce_delay_ms:
                                self._last_publish_time[pad] = now

                                message = self._message_factory.create_message(TOUCH, pad.name)
                                message.tnid = '*'
                                self._log.info('{} touched; publishing message: '.format(pad.name) 
                                        + Fore.GREEN + '{}'.format(message.value))
                                self.publish(message)

                                if self._pixel:
                                    if self._led_task:
                                        self._led_task.cancel()
                                        self._led_task = None
                                    self._led_task = asyncio.create_task(self._flash_led(pad.color, self._led_duration_ms))
                               
                        else:
                            if self._on_release:
                                self._log.info(Fore.BLUE  + '{} released; value: {}'.format( pad.name, value))
                                if self._pixel and self._led_task is None:
                                    if self._led_task:
                                        self._led_task.cancel()
                                        self._led_task = None
                                    self._led_task = asyncio.create_task(self._flash_led(pad.color, self._led_duration_ms))
                            else:
                                self._log.info(Fore.BLACK + '{} released; value: {}'.format( pad.name, value))
                await asyncio.sleep_ms(self._poll_ms)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log.error(
                        'Error in touch poll loop: {}'.format(str(e)))
                await asyncio.sleep_ms(self._poll_ms)

    def is_touched(self, pad):
        return self._is_touched[pad]

    async def _flash_led(self, color, duration_ms=1000):
        '''
        Asynchronously set the color of the pixel for a specified
        period of time, then return to black.
        '''
        self._show_color(color)
        await asyncio.sleep_ms(duration_ms)
        self._show_color(COLOR_BLACK)

    def _show_color(self, color):
        '''
        Set the color of the pixel.
        '''
        if self._pixel:
            self._pixel.show_color(color)

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
#
# from config_loader import ConfigLoader
# from zero_pixel import ZeroPixel
# from config_loader import ConfigLoader
# from message_bus import MessageBus
# from message_factory import MessageFactory
# 
# async def main():
#     _pixel = ZeroPixel()
#     _config = ConfigLoader.configure('relay.yaml')
#     _message_bus     = MessageBus()
#     _message_factory = MessageFactory(_message_bus)
# 
#     publisher = TouchPadPublisher(_config,
#             message_bus=_message_bus,
#             message_factory=_message_factory, 
#             pixel=_pixel)
#     publisher.enable()
#     try:
#         while publisher.enabled:
#             touched = []
#             for pad in publisher.touch_pads:
#                 if publisher.is_touched(pad):
#                     touched.append(pad)
# #           if touched:
# #               print('touched: {}'.format(touched))
#             await asyncio.sleep_ms(200)
#     finally:
#         publisher.stop()
# 
# try:
#     asyncio.run(main())
# except KeyboardInterrupt:
#     print('Ctrl-C caught, exiting...')
# finally:
#     asyncio.new_event_loop()

#EOF
