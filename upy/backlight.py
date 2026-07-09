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
#
# sets the backlight of the UM Explorer shield on or off

from machine import Pin

backlight_pin = Pin(27, Pin.OUT)
backlight_pin.value(0)

# EOF
