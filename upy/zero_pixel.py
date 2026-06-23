#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-04
# modified: 2026-06-23

from pixel import Pixel

from colors import *

class ZeroPixel():
    '''
    Wrapping support for an RGB LED pixel on the Waveshare ESP32-S3 Zero.
    '''
    def __init__(self):
        _brightness = 0.33
        self._pixel = Pixel(pin=21, pixel_count=1, color_order='RGB', brightness=_brightness)
        # GRB?

    def show_color(self, color):
        self._pixel.set_color(0, color)

    def close(self):
        self._pixel.set_color(0, COLOR_BLACK)

#EOF
