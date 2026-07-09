#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-23
# modified: 2026-07-06
#
# ESP-NOW RELAY

import asyncio
import time

from colors import *
from colorama import Fore, Style
from component import Component
from logger import Logger, Level
from event import *
from publisher import Publisher
from push_button import PushButton
from surveyor import Surveyor
from text_generator import TextGenerator

class Initiator(Publisher):
    NAME = 'initiator'
    '''
    Handles physical button interaction to publish a Message onto the MessageBus.
    '''
    def __init__(self, config=None, message_bus=None, message_factory=None, pixel=None, level=Level.INFO):
        Publisher.__init__(
                self,
                Initiator.NAME,
                message_bus=message_bus,
                message_factory=message_factory,
                suppressed=False,
                enabled=False,
                level=level)
        _cfg = config['rros']['initiator']
        self._send_time_ms = None
        self._pixel = pixel
        self._enable_pixel = _cfg['enable_pixel']
        _button_pin = _cfg['pin'] # IO5
        self._button = PushButton(_button_pin, self._send_message)
        self._log.info('ready.')

    def enable(self):
        '''
        When enabled this will locate the Surveyor in the component registry,
        then use it to initiate a ESP-NOW version survey, followed by setting
        the RTC clocks to align with node 1.
        '''
        if self.closed:
            self._log.warn('already closed.')
        elif not self.enabled:
            self._log.info('enabling initiator…')
            super().enable()
            self._log.info(Fore.GREEN + 'initiator ready: creating set RTC task…')
            self._survey_task = asyncio.create_task(self._set_rtc())
            self._log.info(Fore.GREEN + 'creating survey task…')
            self._survey_task = asyncio.create_task(self._survey())
        else:
            self._log.warn('already enabled.')

    def _send_message(self, arg=None):
        '''
        Triggered by the button press.
        '''
        # use sample value
        if self._message_factory.espnow_version == 2:
            value = TextGenerator.generate_lorem_ipsum(1200)
        else:
            value = TextGenerator.generate_food_name()
        message = self._message_factory.create_message(event=BUTTON, value=value)
        self._publish_message(message)

    def _publish_message(self, message):
        '''
        Publishes the message to the Messagebus, adding a '*' tnid so that it
        will be passed to the Relay.
        '''
        message.tnid = '*' # set node target(s) to ALL
        self._log.info("publishing message ID: {}; tnid: {}".format(message.id, message.tnid))
        self._message_bus.publish(message)
        self._log.info("message published.")

    def _show_color(self, color):
        '''
        Set the color of the pixel.
        '''
        if self._pixel and self._enable_pixel:
            self._pixel.show_color(color)

    # set RTC ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    async def _set_rtc(self, duration_ms=1000):
        '''
        Sends a message across the relay to set the RTC of each node to
        that of node 1.
        We don't really care if it's the absolute time, only that the nodes
        share a timestamp (understanding that the relay will introduce a slight
        inaccuracy between nodes).
        '''
        from machine import RTC as _RTC
        _rtc = _RTC()
        dt = _rtc.datetime()
        value = ",".join(str(x) for x in dt)
        message = self._message_factory.create_message(event=RTC, value=value)
        self._log.info("RTC message: {}".format(message))
        self._publish_message(message)

#       dt = tuple(int(x) for x in msg.split(","))
#       rtc.datetime(dt)

    # survey ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    async def _survey(self, duration_ms=1000):
        '''
        Sends a message across the relay to survey each node's installed
        ESP-NOW supported version to determine if it's possible to send
        V2.0 messages of 1470 bytes rather than the 250 bytes of V1.0.
        This also serves as a health status ping.
        '''
        self._show_color(COLOR_AMBER)
        await asyncio.sleep_ms(50)
        _registry = Component.get_registry()
        _surveyor = _registry.get("sub:{}".format(Surveyor.NAME))
        if _surveyor:
            _ok = _surveyor.send(self._show_color)
            # give the survey some time to complete…
            await asyncio.sleep_ms(duration_ms)
            if _ok:
                self._show_color(COLOR_TANGERINE)
            else:
                self._show_color(COLOR_RED)
        else:
            self._show_color(COLOR_RED)
            self._log.warn('no surveyor available.')

#EOF
