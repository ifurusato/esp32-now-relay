#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2021-07-07
# modified: 2024-08-27

import sys
import time
import os
from colorama import Fore, Style

class Util:
    '''
    A collection of static utility methods.
    '''
    def __init__(self):
        raise TypeError("Util may not be instantiated.")

    def __new__(cls):
        raise TypeError("Util may not be instantiated.")

    # ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @staticmethod
    def is_true(value):
        '''
        Returns True if the value is a 1, a "1", "y", "yes", or "true" (with
        case-insensitive matching).
        '''
        if value:
            if isinstance(value, int):
                return value == 1
            else:
                _value = value.lower()
                return _value == "1" or _value == "y" or _value == "yes" or _value == "true"
        return False

    @staticmethod
    def get_timestamp():
        """
        Return an ISO 8601 UTC timestamp.
        """
        year, month, day, hour, minute, second, *_ = time.gmtime()
        return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
            year, month, day, hour, minute, second
        )

    @staticmethod
    def get_formatted_value(value):
        if isinstance(value, float):
            return '{:5.2f}'.format(value)
        else:
            return '{}'.format(value)

    @staticmethod
    def get_formatted_time(label, value):
       if value is None:
           return ''
       elif value > 1000.0:
           return label + ' {:4.3f}s'.format(value/1000.0)
       else:
           return label + ' {:4.3f}ms'.format(value)

    @staticmethod
    def repeat(string, number):
        '''
        Repeat 'string' a given number of times.
        '''
        return (string * (number//len(string) + 1))[:number]

    @staticmethod
    def ellipsis(string, max_length):
        '''
        Repeat 'string' a given number of times.
        '''
        if len(string) < max_length:
            return string
        else:
            return '{}…'.format(string[:max_length-1])

    @staticmethod
    def frange(start=0, stop=1, jump=0.1):
        nsteps = int((stop-start)/jump)
        dy = stop-start
        # f(i) goes from start to stop as i goes from 0 to nsteps
        return [start + float(i)*dy/nsteps for i in range(nsteps)]

    @staticmethod
    def get_class_name_of_method(method):
        return vars(sys.modules[method.__module__])[method.__qualname__.split('.')[0]].__name__

    @staticmethod
    def list_methods(cls):
        '''
        Print the methods of the provided class.
        '''
        print(Fore.CYAN + "methods of class: {}".format(type(cls)) + Style.RESET_ALL)
        method_list = [func for func in dir(cls) if callable(getattr(cls, func))]
        for m in method_list:
            print(Fore.CYAN + '    method:\t' + Fore.YELLOW + '{}'.format(m) + Style.RESET_ALL)

    @staticmethod
    def remap_range(value, in_min, in_max, out_min, out_max):
        '''
        Remaps a value in the input range to the same ratio'd value
        in the output range.
        '''
        # range check
        if in_min == in_max:
            raise ValueError("zero input range.")
        if out_min == out_max:
            raise ValueError("zero output range.")
        # check reversed input range
        _reversed_input = False
        _old_min = min(in_min, in_max)
        _old_max = max(in_min, in_max)
        if not _old_min == in_min:
            _reversed_input = True
        # check reversed output range
        _reversed_output = False
        _new_min = min(out_min, out_max)
        _new_max = max(out_min, out_max)
        if not _new_min == out_min:
            _reversed_output = True
        _portion = (value - _old_min) * (_new_max -_new_min) / (_old_max - _old_min)
        if _reversed_input:
            _portion = (_old_max - value) * (_new_max - _new_min) / (_old_max - _old_min)
        _result = _portion + _new_min
        if _reversed_output:
            _result = _new_max - _portion
        return _result

    @staticmethod
    def clip(value, min_value, max_value):
        '''
        A replacement for numpy's clip():

            _value = numpy.clip(target_value, _min, _max)
        '''
        return min_value if value <= min_value else max_value if value >= max_value else value

    @staticmethod
    def to_bin(decimal):
        return '{0:08b}'.format(decimal)

    @staticmethod
    def to_bin_v2(x):
        return int(bin(x)[2:])

    @staticmethod
    def to_decimal(binary):
        b = str(binary)
        binary_len = len(b)
        decimal = 0
        for x in b:
            binary_len = binary_len - 1
            decimal += pow(2,binary_len) * int(x)
        return decimal

#EOF
