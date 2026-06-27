#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2025 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-27
# modified: 2026-06-27

class Direction:
    _instances = {}

    def __init__(self, id, name):
        self._id = id
        self._name = name
        Direction._instances[id] = self

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @classmethod
    def from_id(cls, id):
        return cls._instances.get(id)

OUTBOUND = Direction( 1, "outbound") # downstream, forward
INBOUND  = Direction(-1, "inbound")  # upstream, reverse

#EOF
