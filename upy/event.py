#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2020-02-21
# modified: 2026-06-22

class Event:
    '''
    A pseudo-enum representing an event type, with a label and a default priority.

    :param id:       unique integer identifier
    :param label:    human-readable label
    :param priority: default priority, 0.0 (lowest) to 1.0 (highest)
    '''
    _registry = []
    _by_id    = {}

    def __init__(self, id, label, priority=0.5):
        self._id       = id
        self._label    = label
        self._priority = priority
        Event._registry.append(self)
        Event._by_id[id] = self

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def priority(self):
        return self._priority

    @classmethod
    def by_id(cls, id):
        return cls._by_id.get(id, None)

    def __eq__(self, other):
        return isinstance(other, Event) and self._id == other._id

    def __hash__(self):
        return hash(self._id)

    def __repr__(self):
        return 'Event({})'.format(self._label)

    @classmethod
    def by_label(cls, label):
        '''
        Looks up and returns an Event instance by its string label using the registry.
        
        :param label: The string label of the event
        :return: The matching Event instance, or None if not registered
        '''
        for event in cls._registry:
            if event.label == label:
                return event
        return None

    @staticmethod
    def all():
        return Event._registry

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
# event instances

FAILURE       = Event(0, 'failure', priority=1.0)
TOF_DISTANCES = Event(1, 'tof',     priority=0.5)
SYSTEM        = Event(2, 'system',  priority=1.0)
STARTUP       = Event(3, 'startup', priority=1.0)
RELAY         = Event(4, 'relay',   priority=1.0)
SURVEY        = Event(5, 'survey',  priority=1.0)

#EOF
