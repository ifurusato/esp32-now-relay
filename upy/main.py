#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-21
# modified: 2026-06-23

import asyncio
import sys, os, gc, sys
import time

from colorama import Fore, Style
from colors import *
from logger import Logger, Level
from config_loader import ConfigLoader
from message_bus import MessageBus
from message_factory import MessageFactory
from event import *
from relay import Relay

# force module reload
for mod in ['main']:
    if mod in sys.modules:
        del sys.modules[mod]

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

IS_TINYS3 = True # otherwise TinyPICO
START_COUNT = 3

pixel = None
log = Logger('main', Level.INFO)

# methods ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

def detect_device_type():
    '''
    Identifies the specific device using firmware machine metadata.

    sys.implementation._machine returns strings like:

       'TinyPICO with ESP32'
       'FeatherS2 with ESP32S2'
       'TinyS3 with ESP32S3' or 'UM TinyS3 with ESP32S3'

    '''
    # safely convert to lowercase to handle any variations in firmware versions
    machine_info = sys.implementation._machine.lower()
    if "tinypico" in machine_info:
        return "TinyPICO"
    elif "feathers2" in machine_info:
        return "FeatherS2"
    elif "tinys3" in machine_info:
        return "TinyS3"
    elif "generic esp32s3" in machine_info:
        return "ESP32S3Zero"
    else:
        print('machine info: {}'.format(machine_info))
        # fallback to checking the underlying chip generation if the device manufacturer altered the string
        return "unknown device (platform info: {})".format(sys.implementation._machine)

def pre_blink():
    '''
    Blinks the LED three times, giving you enough time to interrupt booting the OS.
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
    log.info('RAM free: {:.1f}KB; used: {:.1f}KB; FS total: {:.1f}KB; used: {:.1f}KB; free: {:.1f}KB'.format(
        gc.mem_free()  / 1024,
        gc.mem_alloc() / 1024,
        (s[2] * s[1]) / 1024,
        ((s[2] * s[1]) - (s[4] * s[1])) / 1024,
        (s[4] * s[1]) / 1024
    ))

def identify_device_type():
    '''
    Identifies the type of device and loads the supporting pixel class.
    This is done right at the beginning so we have a pixel to work with.
    '''
    global pixel
    device_type = detect_device_type()
    if device_type == "TinyPICO":
        # TinyPICO uses APA102 (DotStar) RGB LED on pins 2, 3
        from pico_pixel import PicoPixel
        pixel = PicoPixel()
        log.info('device identified as: ' + Fore.GREEN + 'UM TinyPICO')
    elif device_type == "TinyS3":
        # TinyS3 uses a WS2812B (NeoPixel) on pin 18 and has user controlled RF switch
        from s3_pixel import S3Pixel
        pixel = S3Pixel()
        log.info('device identified as: ' + Fore.GREEN + 'UM TinyS3')
    elif device_type == "FeatherS2":
        from feather_pixel import FeatherPixel
        pixel = FeatherPixel()
        # FeatherS2 uses an APA102 on pins 40, 39 and has unique LDO control
        log.info('device identified as: ' + Fore.GREEN + 'UM FeatherS2')

    elif device_type == "ESP32S3Zero":
        from zero_pixel import ZeroPixel
        pixel = ZeroPixel()
        # we're dangerously assuming a generic ESP32-S3 is a Waveshare ESP32-S3 Zero
        log.info('device identified as: ' + Fore.GREEN + 'Waveshare ESP32-S3 Zero ')
    else:
        log.info('device identified as: ' + Fore.GREEN + device_type)

# main ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

_message_bus     = MessageBus()
_message_factory = MessageFactory(_message_bus)
_relay_node      = None

try:

    identify_device_type()
    pre_blink()
    print_sysinfo()

    config = ConfigLoader.configure('config.yaml')
    _relay_node = Relay(
        config=config,
        message_factory=_message_factory,
        pixel=pixel
    )

    # execution processing via asyncio
    log.info("scheduling relay task and starting event loop…")
    asyncio.create_task(_relay_node.run_loop())
    # schedule MessageBus background tasks in the future
    # asyncio.create_task(message_bus.start())
    # keep the main thread alive or run the main loop hook
    asyncio.get_event_loop().run_forever()

except KeyboardInterrupt:
    log.info('interrupted.')
except Exception as e:
    log.error('{} raised: {}'.format(type(e), e))
    sys.print_exception(e)
finally:
    if pixel:
        pixel.close()

#EOF
