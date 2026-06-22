#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-22
# modified: 2026-06-22

from machine import SoftSPI, Pin
from dotstar import DotStar

from colors import *

class FeatherPixel:
    '''
    Wrapping support for the APA102 DotStar pixel on the Unexpected Maker FeatherS2.
    '''
    def __init__(self):
        # Explicitly configure and turn on the custom LDO power rail for the LED
        self._power_pin = Pin(21, Pin.OUT)
        self._power_pin.value(1)
        # FeatherS2 DotStar hardware configuration: CLK=45, DATA=40, MISO=37 (unused, but required by SoftSPI)
        spi = SoftSPI(sck=Pin(45), mosi=Pin(40), miso=Pin(37))
        self._dotstar = DotStar(spi, 1, brightness=0.3)

    def show_color(self, color):
        '''
        Updates the single pixel to the specified color tuple (R, G, B).
        '''
        self._dotstar[0] = color

    def close(self):
        '''
        Resets the pixel color to black, deinitializes SPI, and drops the LDO power rail.
        '''
        self._dotstar[0] = COLOR_BLACK
        self._dotstar.deinit()
        self._power_pin.value(0)

# EOF
