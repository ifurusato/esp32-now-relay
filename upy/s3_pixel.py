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

import tinys3
from pixel import Pixel

from colors import *

class S3Pixel():
    '''
    Wrapping support for an RGB LED pixel on the Tiny S3.
    '''
    def __init__(self):
        _pixel_pin = tinys3.RGB_DATA
        _brightness = 0.33
        self._pixel = Pixel(pin=_pixel_pin, pixel_count=1, color_order='GRB', brightness=_brightness)
        tinys3.set_pixel_power(1)

    def show_color(self, color):
        self._pixel.set_color(0, color)

    def close(self):
        self._pixel.set_color(0, COLOR_BLACK)

#EOF
