#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2021-06-29
# modified: 2026-07-27

from collections import OrderedDict
from colorama import Fore, Style

from logger import Logger, Level
from config_error import ConfigurationError

class ComponentRegistry:
    '''
    Maintains a registry of all Components, in the order in which they were created.
    '''
    def __init__(self, level=Level.INFO):
        self._log = Logger("comp-registry", level)
        self._verbose = False
        self._dict = OrderedDict()

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def filter_by_type(self, cls):
        '''
        Return a dict of all components in the registry that are instances of cls.
        '''
        return [v for v in self._dict.values() if isinstance(v, cls)]

    def count_by_type(self, cls):
        '''
        Return the count of components of a given type.
        '''
        return len(self.filter_by_type(cls))

    @property
    def names(self):
        '''
        Returns the set of keys to the registry as a list.
        '''
        return list(self._dict.keys())

    def length(self):
        '''
        Return the number of entries in the dictionary.
        '''
        return len(self._dict)

    def empty(self):
        '''
        Return True if the dictionary is empty.
        '''
        return len(self._dict) == 0

    @staticmethod
    def is_publisher(component):
        return any(cls.__name__ == "Publisher" for cls in component.__class__.mro())

    @staticmethod
    def is_subscriber(component):
        return any(cls.__name__ == "Subscriber" for cls in component.__class__.mro())

    @staticmethod
    def is_behaviour(component):
        return any(cls.__name__ == "Behaviour" for cls in component.__class__.mro())

    @staticmethod
    def is_multiple_inheritor(component):
        '''
        Returns True if the component multiply inherits Publisher, Subscriber,
        and/or Behaviour.
        '''
        return sum([
            ComponentRegistry.is_publisher(component),
            ComponentRegistry.is_subscriber(component),
            ComponentRegistry.is_behaviour(component)]) >= 2

    def add(self, component):
        '''
        Add a component to the registry using its name, generating either a
        warning or raising a ConfigurationError if a like-named component
        already exists in the registry.
        '''
        if component.name in self._dict:
            existing = self._dict.get(component.name)
            if ComponentRegistry.is_multiple_inheritor(existing):
                if self._verbose:
                    self._log.info(Style.DIM + 'multiple-inheritor component \'{}\' already in registry.'.format(component.name))
                return
            else:
                raise ConfigurationError('component \'{}\' already in registry.'.format(component.name))
        from component import Component
        if not isinstance(component, Component):
            raise TypeError('argument \'{}\' is not a component.'.format(type(component)))
        else:
            self._dict[component.name] = component
            if self._verbose:
                self._log.info(Style.DIM + 'added component \'{}\' ({}) to registry ({:d} total).'.format(component.name, component.uuid, len(self._dict)))

    def has(self, name):
        '''
        Returns True if the name is found in the registry.
        '''
        return name in self._dict

    def clear(self):
        '''
        Clear the registry dict.
        '''
        self._dict.clear()

    def remove(self, name):
        '''
        Remove a component from the registry by name. Logs a warning if the
        name is not found.
        '''
        if name in self._dict:
            removed = self._dict.pop(name)
            if self._verbose:
                self._log.info("removed component '{}' ({}) from registry ({} remaining).".format(name, removed.uuid, len(self._dict)))
            return removed
        else:
            self._log.warn("cannot remove '{}'; not found in registry.".format(name))
            return None

    def deregister(self, component):
        for name, obj in list(self._dict.items()):
            if obj is component:
                self._log.debug("removing '{}' from registry…".format(name))
                del self._dict[name]
                return True
        return False

    def get(self, name):
        '''
        Return the component by name.
        '''
        return self._dict.get(name)

    def print_registry(self):
        '''
        Print the registry to the log.
        '''
        self._log.info('component list:')
        self._log.info(
            Style.DIM +
            '{:<20}{:<28}{:<10}{:<10}'.format(
                'id', 'class', 'enabled', 'released'
            )
        )
        for _name, _component in self._dict.items():
            self._log.info(
                '{:<20}{}{:<28}{}{}{:<10}{}{:<10}'.format(
                    _name,
                    Fore.YELLOW,
                    _component.classname,
                    Fore.CYAN,
                    Style.NORMAL if _component.enabled else Style.DIM,
                    str(_component.enabled),
                    Style.NORMAL if _component.released else Style.DIM,
                    str(_component.released)
                )
            )

    def count_open_components(self):
        '''
        Returns the number of components in the registry that are not closed.
        '''
        return sum(1 for c in self._dict.values() if not c.closed)

    def all(self):
        '''
        Return the backing registry as a dict.
        '''
        return self._dict

    def items(self):
        '''
        Return the items contained in the registry.
        '''
        return self._dict.items()

    def __iter__(self):
        '''
        Return an iterator over the values in the registry.
        '''
        return iter(self._dict.values())

#EOF
