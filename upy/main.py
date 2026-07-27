#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-21
# modified: 2026-07-27

import sys

# force module reload for local modules
for mod in [ 'main', 'touch_pad_app', 'relay' ]:
    if mod in sys.modules:
        del sys.modules[mod]

import os
import gc
import time
from colorama import Fore, Style

from colors import *
from logger import Logger, Level
from config_loader import ConfigLoader
from networking import Networking
from relay import Relay
from touch_pad_app import TouchPadApp

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

START_COUNT = 3

log = Logger('main', Level.INFO)

def detect_device_type():
    '''
    Identifies the specific device using firmware machine metadata.
    '''
    machine_info = sys.implementation._machine.lower()
    if "tinypico" in machine_info:
        return "tinypico"
    elif "feathers2" in machine_info:
        return "feathers2"
    elif "tinys3" in machine_info:
        return "tinys3"
    elif "generic esp32s3" in machine_info:
        return None
    else:
        log.info("unknown device (platform info: {})".format(sys.implementation._machine))
        return None

def load_pixel_implementation(config, device_type):
    '''
    Loads the supporting pixel class for the given device type.
    '''
    if device_type == "tinypico":
        from pico_pixel import PicoPixel
        log.info('device identified as: ' + Fore.GREEN + 'UM TinyPICO')
        return PicoPixel()
    elif device_type == "tinys3":
        from s3_pixel import S3Pixel
        log.info('device identified as: ' + Fore.GREEN + 'UM TinyS3')
        return S3Pixel()
    elif device_type == "feathers2":
        from feather_pixel import FeatherPixel
        log.info('device identified as: ' + Fore.GREEN + 'UM FeatherS2')
        return FeatherPixel()
    elif device_type == "zero":
        from zero_pixel import ZeroPixel
        log.info('device identified as: ' + Fore.GREEN + 'Waveshare ESP32-S3 Zero')
        return ZeroPixel()
    elif device_type == "super-mini":
        from super_mini_pixel import SuperMiniPixel
        log.info('device identified as: ' + Fore.GREEN + 'ESP32-S3 Super Mini')
        return SuperMiniPixel()
    return None

def pre_blink(pixel):
    '''
    Blinks the LED, giving enough time to interrupt booting the OS.
    '''
    for i in range(START_COUNT):
        log.info('[{}/{}] starting…'.format(i + 1, START_COUNT))
        pixel.show_color(COLOR_DARK_CYAN)
        time.sleep_ms(50)
        pixel.show_color(COLOR_BLACK)
        time.sleep_ms(950)

def print_sysinfo():
    gc.collect()
    s = os.statvfs('/')
    log.info('RAM free: {:.1f}KB; used: {:.1f}KB; FS used/total: {:.1f}KB/{:.1f}KB; free: {:.1f}KB'.format(
        gc.mem_free() / 1024,
        gc.mem_alloc() / 1024,
        ((s[2] * s[1]) - (s[4] * s[1])) / 1024,
        (s[2] * s[1]) / 1024,
        (s[4] * s[1]) / 1024
    ))

def run():
    pixel = None
    try:
        config = ConfigLoader.configure('relay.yaml')
        networking = Networking()
        mac_address = networking.mac_address
        device_type = detect_device_type()
        log.info('detected device: {}{}{}'.format(Fore.GREEN, device_type, Fore.CYAN))

        pixel = load_pixel_implementation(config, device_type)
        if not pixel:
            device_catalog = config['rros']['relay']['devices']
            node_index, node_profile = Relay.find_device_by_mac(device_catalog, mac_address)
            device_type = node_profile['device']
            pixel = load_pixel_implementation(config, device_type)
            log.info('device identifier: {}{}{} (via MAC address)'.format(Fore.GREEN, device_type, Fore.CYAN))

        if not pixel:
            log.warn('no pixel identified for device type: {}'.format(device_type))

        if pixel:
            pre_blink(pixel)

        print_sysinfo()

        app = TouchPadApp(config=config, networking=networking, pixel=pixel)
        app.enable()

    except KeyboardInterrupt:
        log.info('interrupted in main.')
    except Exception as e:
        log.error('{} raised: {}'.format(type(e), e))
        sys.print_exception(e)

if __name__ in ('__main__', 'main'):
    run()

#EOF
