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

from logger import Logger, Level
from component_registry import ComponentRegistry
from uuid import UUID, uuid4

class Component:
    __registry = None # singleton
    '''
    A basic component providing enabled, suppressed and closed state flags.
    This is a simplification of the CPython version.

    All Components are automatically added to the ComponentRegistry, which is
    an alternative means of gaining access to them within the application, by
    name as key. Upon closing, close_registry() should be called to clear the
    registry and destroy its instance.

    :param name:         either the component name, or a Logger instance
    :param suppressed:   initial suppressed state (default False)
    :param enabled:      initial enabled state (default False)
    '''
    def __init__(self, name, suppressed=False, enabled=False, level=Level.INFO):
        if name is None:
            raise ValueError('null name argument.')
        elif isinstance(name, str):
            self._name   = name
            self._log    = Logger(self._name, level)
        elif isinstance(name, Logger):
            self._log    = name
            self._name   = self._log.name
        else:
            raise ValueError('invalid name (or Logger) argument type: {}'.format(type(name)))
        super().__init__()
        self._uuid       = uuid4()
        self._suppressed = suppressed
        self._enabled    = enabled
        registry = Component._registry()
        if not registry.has(self._log.name):
            registry.add(self)
        self._closed     = False

    @staticmethod
    def _registry():
        '''
        Create and/or return the singleton instance of the component registry.
        '''
        if Component.__registry is None:
            Component.__registry = ComponentRegistry()
        return Component.__registry

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @staticmethod
    def get_registry():
        return Component.__registry

    @property
    def uuid(self):
        return self._uuid

    @property
    def name(self):
        return self._name

    @property
    def enabled(self):
        return self._enabled

    @property
    def disabled(self):
        return not self._enabled

    @property
    def suppressed(self):
        return self._suppressed

    @property
    def released(self):
        return not self._suppressed

    @property
    def is_active(self):
        '''
        Returns True if enabled and not suppressed.
        '''
        return self._enabled and not self._suppressed

    @property
    def closed(self):
        return self._closed

    @property
    def classname(self):
        '''
        Return the name of this Component's class.
        '''
        return type(self).__name__

    def suppress(self):
        self._suppressed = True
        self._log.info('suppressed.')

    def release(self):
        self._suppressed = False
        self._log.info('released.')

    def enable(self):
        if self._closed:
            self._log.warn('already closed.')
        elif not self._enabled:
            self._enabled = True
            self._log.debug('enabled.')
        else:
            self._log.warn('already enabled.')

    def disable(self):
        if self._enabled:
            self._enabled = False
            self._log.debug('disabled.')
        else:
            self._log.warn('already disabled.')

    def close(self):
        if not self._closed:
            if self.enabled:
                self.disable()
            Component.__registry.deregister(self)
            self._closed = True
            self._log.debug('closed.')
        else:
            self._log.warn('already closed.')

    @staticmethod
    def close_registry():
        '''
        To be called at application close, to clear and eliminate any
        references to the component registry.
        '''
        if Component.__registry is not None:
            Component.__registry.clear()
            Component.__registry = None

#EOF
