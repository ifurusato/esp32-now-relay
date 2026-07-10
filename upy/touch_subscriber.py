#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-07-05
# modified: 2026-07-10
#
# ESP-NOW RELAY

import asyncio
from colorama import Fore, Style

from logger import Level
from event import TOUCH
from colors import *
from subscriber import Subscriber
from explorer_button import ExplorerButton

class TouchSubscriber(Subscriber):
    NAME = 'touch'
    '''
    A subscriber that receives TOUCH event messages and decodes their string value
    back into ExplorerButton pseudo-enum instances for further action.

    This is meant to be installed on both the initiator and endpoint nodes.
    '''
    def __init__(self, config, message_bus, pixel, level=Level.INFO):
        Subscriber.__init__(self, TouchSubscriber.NAME, suppressed=False, enabled=True, message_bus=message_bus, level=level)
        self._config   = config
        self._pixel    = pixel
        self._led_task = None
        self.add_event(TOUCH)
        self._log.info('ready.')

    async def process_message(self, message):
        '''
        Decodes the message payload back into an ExplorerButton instance.
        '''
        self._log.info('process message: ' + Fore.GREEN + '{}'.format(message))
        button_name = message.value
        button = ExplorerButton.by_name(button_name)
        if button is not None:
            await self.handle_button_press(button, message)
        else:
            self._log.error('received unknown button name payload: {}'.format(button_name))

    async def handle_button_press(self, button, message):
        '''
        Action performed when a valid ExplorerButton is identified.

        This method can be overridden by subclasses to perform actions
        depending upon the button.
        '''
        if self._led_task is not None:
            self._led_task.cancel()
        self._led_task = asyncio.create_task(self._flash_led(button.color, 1000))

    # utility ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def _show_color(self, color):
        '''
        Set the color of the pixel.
        '''
        if self._pixel:
            self._pixel.show_color(color)

    async def _flash_led(self, color, duration_ms=1000):
        '''
        Asynchronously set the color of the pixel for a specified
        period of time, then return to black.
        '''
        try:
            self._show_color(color)
            await asyncio.sleep_ms(duration_ms)
        except asyncio.CancelledError:
            pass
        finally:
            self._show_color(COLOR_BLACK)

#EOF
