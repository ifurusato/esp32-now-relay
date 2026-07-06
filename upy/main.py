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
from networking import Networking
from config_loader import ConfigLoader
from message_bus import MessageBus
from message_factory import MessageFactory
from gateway import NetworkGateway
from surveyor import Surveyor
from event import *
from relay import Relay

# force module reload
for mod in ['main']:
    if mod in sys.modules:
        del sys.modules[mod]

# ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

IS_TINYS3 = True # otherwise TinyPICO
START_COUNT = 1

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
        return "tinypico"
    elif "feathers2" in machine_info:
        return "feathers2"
    elif "tinys3" in machine_info:
        return "tinys3"
    elif "generic esp32s3" in machine_info:
        return None # likely "zero"
    else:
        # fallback to checking the underlying chip generation if the device manufacturer altered the string
        _log.info("unknown device (platform info: {})".format(sys.implementation._machine))
        return None

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
    log.info('RAM free: {:.1f}KB; used: {:.1f}KB; FS used/total: {:.1f}KB/{:.1f}KB; free: {:.1f}KB'.format(
        gc.mem_free()  / 1024,                   # ram free
        gc.mem_alloc() / 1024,                   # ram used
        ((s[2] * s[1]) - (s[4] * s[1])) / 1024,  # fs used
        (s[2] * s[1]) / 1024,                    # fs total
        (s[4] * s[1]) / 1024                     # fs free
    ))

def load_pixel_implementation(config, device_type):
    '''
    Loads the supporting pixel class for the given device type.
    This is done right at the beginning so we have a pixel to work with.
    '''
    global pixel
    if device_type == "tinypico":
        # TinyPICO uses APA102 (DotStar) RGB LED on pins 2, 3
        from pico_pixel import PicoPixel
        pixel = PicoPixel()
        log.info('device identified as: ' + Fore.GREEN + 'UM TinyPICO')
        return True
    elif device_type == "tinys3":
        # TinyS3 uses a WS2812B (NeoPixel) on pin 18 and has user controlled RF switch
        from s3_pixel import S3Pixel
        pixel = S3Pixel()
        log.info('device identified as: ' + Fore.GREEN + 'UM TinyS3')
        return True
    elif device_type == "feathers2":
        from feather_pixel import FeatherPixel
        pixel = FeatherPixel()
        # FeatherS2 uses an APA102 on pins 40, 39 and has unique LDO control
        log.info('device identified as: ' + Fore.GREEN + 'UM FeatherS2')
        return True
    elif device_type == "zero":
        from zero_pixel import ZeroPixel
        pixel = ZeroPixel()
        # we make a dangerous assumption that this is a Waveshare ESP32-S3 Zero
        log.info('device identified as: ' + Fore.GREEN + 'Waveshare ESP32-S3 Zero')
        return True
    return False

# main ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

try:

    _config = ConfigLoader.configure('config.yaml')

    _message_bus     = MessageBus()
    _message_factory = MessageFactory(_message_bus)
    _networking      = Networking()
    mac_address      = _networking.mac_address
    device_type      = detect_device_type()

    loaded_pixel = load_pixel_implementation(_config, device_type)
    if not loaded_pixel:
        # try again with MAC address and config 
        device_catalog = _config['rros']['relay']['devices']
        node_index, node_profile = Relay.find_device_by_mac(device_catalog, mac_address)
        device_type = node_profile['device']
        loaded_pixel = load_pixel_implementation(_config, device_type)
        log.info('device identifier: {}{}{} (via MAC address)'.format(Fore.GREEN, device_type, Fore.CYAN))

    if pixel:
        pre_blink()
    print_sysinfo()

    # create relay
    _relay = Relay(
        config=_config,
        networking=_networking,
        message_bus=_message_bus,
        message_factory=_message_factory,
        pixel=pixel
    )
    # create surveyor
    log.info("creating surveyor…")
    _surveyor = Surveyor(_config, _relay.index, _networking, _message_bus, _message_factory)
    # create gateway
    _gateway = NetworkGateway(_config, _relay.index, _message_bus, _message_factory, _relay)

    if _relay.is_initiator():
        log.info("establishing initiator…")
        from initiator import Initiator
        _initiator = Initiator(_config, _message_bus, _message_factory)

        log.info("creating touch publisher…")
        from touch_publisher import TouchPublisher

        _touch = TouchPublisher(_config, _message_bus, _message_factory)
        _touch.enable()
    elif _relay.is_endpoint():
        log.info("creating touch subscriber…")
        from touch_subscriber import TouchSubscriber

        _touch = TouchSubscriber(_config, pixel, _message_bus)
        _touch.enable()

    # execution processing via asyncio
    log.info("scheduling relay task and starting event loop…")
    _relay.enable()
#   asyncio.create_task(_relay.run_loop())
    # keep the main thread alive or run the main loop hook
#   asyncio.get_event_loop().run_forever()
    # keep the main thread alive using the MessageBus
    _message_bus.enable()

except KeyboardInterrupt:
    log.info('interrupted.')
except Exception as e:
    log.error('{} raised: {}'.format(type(e), e))
    sys.print_exception(e)
finally:
    if pixel:
        pixel.close()

#EOF
