#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-21
# modified: 2026-07-27

import sys
from colorama import Fore, Style

from colors import *
from event import *
from logger import Logger, Level
from component import Component
from message_bus import MessageBus
from message_factory import MessageFactory
from gateway import NetworkGateway
from surveyor import Surveyor
from relay import Relay

class TouchPadApp:
    NAME = 'app'


    def __init__(self, config, networking, pixel=None, level=Level.INFO):
        self._log = Logger(TouchPadApp.NAME, level=level)
        self._config        = config
        _cfg = config['rros']['touch_pad_app']
        self._use_explorer  = _cfg['use_explorer'] # if true use UM Explorer rather than TouchPad
        self._networking    = networking
        self._pixel         = pixel
        self._enabled       = False
        self._initiator        = None
        self._touch_publisher  = None
        self._touch_subscriber = None
        self._rtc_subscriber   = None
        # components
        self._message_bus = MessageBus()
        self._message_factory = MessageFactory(self._message_bus)
        self._relay = Relay(
            config=self._config,
            networking=self._networking,
            message_factory=self._message_factory,
            pixel=self._pixel
        )
        self._log.info("creating gateway…")
        self._gateway = NetworkGateway(
            self._config,
            self._message_bus,
            self._message_factory,
            self._relay
        )
        self._log.info("creating surveyor…")
        self._surveyor = Surveyor(
            self._config,
            self._networking,
            self._message_bus,
            self._message_factory,
            self._relay
        )
        if self._relay.is_initiator():
            self._log.info("establishing initiator…")
            from initiator import Initiator

            self._initiator = Initiator(
                self._config,
                self._message_bus,
                self._message_factory,
                self._pixel
            )

            if self._use_explorer:
                self._log.info("creating touch publisher…")
                from touch_publisher import TouchPublisher

                self._touch_publisher = TouchPublisher(
                    self._config,
                    self._message_bus,
                    self._message_factory
                )
            else:
                self._log.info("creating touch pad publisher…")
                from touch_pad_publisher import TouchPadPublisher

                self._touch_publisher = TouchPadPublisher(
                    config=self._config,
                    message_bus=self._message_bus,
                    message_factory=self._message_factory,
                    pixel=self._pixel
                )

        elif self._relay.is_endpoint():
            self._log.info("creating touch subscriber…")
            from touch_subscriber import TouchSubscriber

            self._touch_subscriber = TouchSubscriber(
                self._config,
                self._message_bus,
                self._pixel
            )

        if not self._relay.is_initiator():
            from rtc_subscriber import RtcSubscriber

            self._rtc_subscriber = RtcSubscriber(self._config, self._message_bus)

        self._log.info('ready.')

    def enable(self):
        if not self._enabled:
            self._enabled = True
            self._log.info('enabling…')
            self._gateway.enable()
            self._relay.enable()
            if self._initiator:
                self._initiator.enable()
            if self._touch_publisher:
                self._touch_publisher.enable()
            if self._touch_subscriber:
                self._touch_subscriber.enable()
            if self._rtc_subscriber:
                self._rtc_subscriber.enable()
            # print component registry
            registry = Component.get_registry()
            registry.print_registry()
            self._log.info('enabled.')
            try:
                self._log.info(Fore.WHITE + "starting message bus…")
                # blocking
                self._message_bus.enable()
            except KeyboardInterrupt:
                self._log.info('interrupted.')
            except Exception as e:
                self._log.error('{} raised: {}'.format(type(e), e))
                sys.print_exception(e)
            finally:
                self.close()
            self._log.info('enabled.')
        else:
            self._log.warn("already enabled.")

    def close(self):
        if self._message_bus:
            self._message_bus.close()
            self._message_bus = None
        if self._pixel:
            self._pixel.close()
            self._pixel = None
        Component.close_registry()
        self._log.info('closed component registry.')

#EOF
