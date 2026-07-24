#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-21 from ExplorerButton
# modified: 2026-07-21

from colors import *

class TouchPad:
    '''
    Enumerates the touch sensitive buttons on the RobotPad controller.
    '''
    _registry = []
    _by_id = {}
    _by_pin = {}

    def __init__(self, id, name, color, pin):
        self._id = id
        self._name = name
        self._color = color
        self._pin = pin
        TouchPad._registry.append(self)
        TouchPad._by_id[id] = self
        TouchPad._by_pin[pin] = self

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def color(self):
        return self._color

    @property
    def pin(self):
        return self._pin

    @classmethod
    def by_id(cls, id):
        return cls._by_id.get(id, None)

    @classmethod
    def by_pin(cls, pin):
        return cls._by_pin.get(pin, None)

    def __eq__(self, other):
        return isinstance(other, TouchPad) and self._id == other._id

    def __hash__(self):
        return hash(self._id)

    def __repr__(self):
        return 'TouchPad({})'.format(self._name)

    @classmethod
    def by_name(cls, name):
        for button in cls._registry:
            if button.name == name:
                return button
        return None

    @staticmethod
    def all():
        return TouchPad._registry


BTN_3  = TouchPad( 0, '3',  COLOR_EMERALD,      9)
BTN_2  = TouchPad( 1, '2',  COLOR_GREEN,        8)
BTN_1  = TouchPad( 2, '1',  COLOR_PEAR,         7)
BTN_DN = TouchPad( 3, 'DN', COLOR_AMBER,        6)
BTN_LT = TouchPad( 4, 'LT', COLOR_RED,          2)
BTN_RT = TouchPad( 5, 'RT', COLOR_YELLOW,       5)
BTN_4  = TouchPad( 6, '4',  COLOR_ORANGE,       4)
BTN_UP = TouchPad( 7, 'UP', COLOR_TANGERINE,    1)
BTN_B  = TouchPad( 8, 'B',  COLOR_VIOLET,      11)
BTN_A  = TouchPad( 9, 'A',  COLOR_BLUE,        10)
BTN_Y  = TouchPad(10, 'Y',  COLOR_SKY_BLUE,    13)
BTN_X  = TouchPad(11, 'X',  COLOR_CYAN,        12)

#EOF
