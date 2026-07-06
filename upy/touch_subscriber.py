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

from logger import Level
from event import TOUCH
from colors import *
from subscriber import Subscriber
from explorer_button import ExplorerButton
from colorama import Fore

class TouchSubscriber(Subscriber):
    NAME = 'touch'
    '''
    A subscriber that receives TOUCH event messages and decodes their string value
    back into ExplorerButton pseudo-enum instances for further action.
    '''
    def __init__(self, config, pixel, message_bus, level=Level.INFO):
        Subscriber.__init__(self, TouchSubscriber.NAME, message_bus, level)
        self._config = config
        self._pixel  = pixel
        self.add_event(TOUCH)
        # map each ExplorerButton to its corresponding color
        self._button_colors = {
            ExplorerButton.by_name('A'):     COLOR_BLUE,
            ExplorerButton.by_name('B'):     COLOR_VIOLET,
            ExplorerButton.by_name('X'):     COLOR_CYAN,
            ExplorerButton.by_name('Y'):     COLOR_SKY_BLUE,
            ExplorerButton.by_name('UP'):    COLOR_TANGERINE,
            ExplorerButton.by_name('DN'):    COLOR_AMBER,
            ExplorerButton.by_name('LT'):    COLOR_RED,
            ExplorerButton.by_name('RT'):    COLOR_YELLOW,
            ExplorerButton.by_name('1'):     COLOR_APPLE,
            ExplorerButton.by_name('2'):     COLOR_GREEN,
            ExplorerButton.by_name('3'):     COLOR_EMERALD,
            ExplorerButton.by_name('4'):     COLOR_ORANGE,
        }
        self._log.info('ready.')

    async def process_message(self, message):
        '''
        Decodes the message payload back into an ExplorerButton instance.
        '''
        button_name = message.value
        button = ExplorerButton.by_name(button_name)
        if button is not None:
            await self._handle_button_press(button, message)
        else:
            self._log.error('Received unknown button name payload: {}'.format(button_name))

    async def _handle_button_press(self, button, message):
        '''
        Action performed when a valid ExplorerButton is identified.
        '''
        color = self._button_colors.get(button)
        if color:
            self._log.info('setting color {} for button: {}'.format(color.name, button))
            self._pixel.show_color(color)
        else:
            self._log.warn('no color for button: {}'.format(button))
        self._log.info('rx: button={} ID={} (age={}ms)'.format(
            Fore.GREEN + button.name + Fore.RESET,
            button.id,
            message.age_ms
        ))

#EOF
