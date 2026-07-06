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

class ExplorerButton:
    '''
    Enumerates the touch sensitive buttons on the Unexpected Maker Explorer
    Shield, a gamepad-like device built around an ESP32 TinyPICO.
    '''
    _registry = []
    _by_id = {}
    _by_mask = {}

    def __init__(self, id, name, mask):
        self._id = id
        self._name = name
        self._mask = mask
        ExplorerButton._registry.append(self)
        ExplorerButton._by_id[id] = self
        ExplorerButton._by_mask[mask] = self

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def mask(self):
        return self._mask

    @classmethod
    def by_id(cls, id):
        return cls._by_id.get(id, None)

    @classmethod
    def by_mask(cls, mask):
        return cls._by_mask.get(mask, None)

    def __eq__(self, other):
        return isinstance(other, ExplorerButton) and self._id == other._id

    def __hash__(self):
        return hash(self._id)

    def __repr__(self):
        return 'ExplorerButton({})'.format(self._name)

    @classmethod
    def by_name(cls, name):
        for button in cls._registry:
            if button.name == name:
                return button
        return None

    @staticmethod
    def all():
        return ExplorerButton._registry

# ExplorerButton instances coupling names to hardware bitmasks
BTN_3  = ExplorerButton( 0,  '3',    1)
BTN_2  = ExplorerButton( 1,  '2',    2)
BTN_1  = ExplorerButton( 2,  '1',    4)
BTN_DN = ExplorerButton( 3, 'DN',    8)
BTN_LT = ExplorerButton( 4, 'LT',   16)
BTN_RT = ExplorerButton( 5, 'RT',   32)
BTN_4  = ExplorerButton( 6,  '4',   64)
BTN_UP = ExplorerButton( 7, 'UP',  128)
BTN_B  = ExplorerButton( 8,  'B',  256)
BTN_A  = ExplorerButton( 9,  'A',  512)
BTN_Y  = ExplorerButton(10,  'Y', 1024)
BTN_X  = ExplorerButton(11,  'X', 2048)

#EOF
