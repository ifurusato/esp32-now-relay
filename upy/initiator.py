#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-23
# modified: 2026-06-23

import time

from colorama import Fore, Style
from logger import Logger, Level
from event import *
from publisher import Publisher
from push_button import PushButton
from food_name_generator import FoodNameGenerator

class Initiator(Publisher):
    NAME = 'initiator'
    '''
    Handles physical button interaction to publish a Message onto the MessageBus.
    '''
    def __init__(self, config=None, message_bus=None, message_factory=None, level=Level.INFO):
        Publisher.__init__(
                self,
                Initiator.NAME,
                message_bus=message_bus,
                message_factory=message_factory,
                suppressed=False,
                enabled=True,
                level=level)
        _cfg = config['rros']['initiator']
        self._send_time_ms = None
        _button_pin = _cfg['pin'] # IO5
        self._button = PushButton(_button_pin, self._send_message)
        self._log.info('ready.')

    def _send_message(self, arg=None):
        '''
        Triggered by the button press.
        '''
        # use sample value
        value = FoodNameGenerator.generate()
        message = self._message_factory.create_message(event=RELAY, value=value)
        message.tnid = '*' # set node target(s) to ALL
        self._log.info("publishing message ID: {}; tnid: {}".format(message.id, message.tnid))
        self._message_bus.publish(message)
        self._log.info("message published.")

#EOF
