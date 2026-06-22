#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-04
# modified: 2026-06-04

from machine import SoftSPI, Pin
import tinypico as TinyPICO
from dotstar import DotStar

from colors import *

class PicoPixel():
    '''
    Wrapping support for a DotStar pixel on the TinyPICO.
    '''
    def __init__(self):
        spi = SoftSPI(sck=Pin(TinyPICO.DOTSTAR_CLK), mosi=Pin(TinyPICO.DOTSTAR_DATA), miso=Pin(TinyPICO.SPI_MISO))
        self._dotstar = DotStar(spi, 1, brightness=0.3)
        TinyPICO.set_dotstar_power(True)

    def show_color(self, color):
        self._dotstar[0] = color

    def close(self):
        self._dotstar[0] = COLOR_BLACK
        self._dotstar.deinit()

#EOF
