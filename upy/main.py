#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-04
# modified: 2026-06-22

import asyncio
import sys, os, gc, sys
import network
import time
import ubinascii

from colorama import Fore, Style
from colors import *
from logger import Logger, Level
from config_loader import ConfigLoader
from message import Message
from message_bus import MessageBus
from message_factory import MessageFactory
from event import *
from relay import Relay
import yaml

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
    Identifies the specific Unexpected Maker device using firmware machine metadata.
    '''
    # sys.implementation._machine returns strings like:
    # 'TinyPICO with ESP32'
    # 'FeatherS2 with ESP32S2'
    # 'TinyS3 with ESP32S3' or 'UM TinyS3 with ESP32S3'
    
    # Safely convert to lowercase to handle any variations in firmware versions
    machine_info = sys.implementation._machine.lower()
    if "tinypico" in machine_info:
        return "TinyPICO"
    elif "feathers2" in machine_info:
        return "FeatherS2"
    elif "tinys3" in machine_info:
        return "TinyS3"
    else:
        # fallback to checking the underlying chip generation if the device manufacturer altered the string
        return "unknown device (platform info: {})".format(sys.implementation._machine)

def mac_to_bytes(mac_str):
    '''
    Converts a colon-separated hex MAC string into a bytes object.
    '''
    clean_hex = mac_str.replace(':', '')
    return ubinascii.unhexlify(clean_hex)

def pre_blink():
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
    else:
        log.info('device identified as: ' + Fore.GREEN + device_type)

def receive_message(message):
    global _send_time_ms
    rtt_ms = time.ticks_diff(time.ticks_ms(), _send_time_ms)
    _send_time_ms = None
    log.info("🌸 round trip time: {} ms on message: {}".format(rtt_ms, message))

def send_message(value):
    print('🌸 send message: {}'.format(value))
    global _send_time_ms
    if _downstream_mac:
        _send_time_ms = time.ticks_ms()
        log.info("first node detected; sending initialization payload downstream.")
        _message = _message_factory.create_message(event=RELAY, value='message content')
        # set callback to receive inbound message
        _relay_node.set_receive_callback(receive_message)
        # send outbound (direction=1) down the chain
        _relay_node.send_message_obj(_downstream_mac, 1, _message)

# main ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

_send_time_ms    = None
_upstream_mac    = None
_downstream_mac  = None
_message_bus     = MessageBus()
_message_factory = MessageFactory(_message_bus)
_relay_node      = None

try:

    identify_device_type()
    pre_blink()
    print_sysinfo()

    # 1. determine local MAC address
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    local_mac_bytes = wlan.config('mac')
    local_mac_str = ubinascii.hexlify(local_mac_bytes, ':').decode('utf-8')
    log.info("booting device; local MAC: {}".format(local_mac_str))

    # 2. load and parse the topology catalog
    config = ConfigLoader.configure('config.yaml')
    device_list = config.get('devices', [])
    total_devices = len(device_list)
    log.info("loaded configuration for {} devices.".format(total_devices))

    # 3. find this device's position in the catalog
    my_index = None
    for i, device in enumerate(device_list):
        if device.get('mac').lower() == local_mac_str.lower():
            my_index = i
            break
    if my_index is None:
        pixel.show_color(COLOR_RED)
        raise Exception("local MAC address not found in topology catalog.")
    else:
        pixel.show_color(COLOR_GREEN)
        log.info('this device identified as: ' 
                + Fore.GREEN + '{}'.format(device_list[my_index].get('name')))

    time.sleep(3)
    pixel.show_color(COLOR_BLACK)

    # 4. build neighbor routing maps
    is_endpoint = False
    if my_index > 0:
        _upstream_mac = mac_to_bytes(device_list[my_index - 1].get('mac'))
    if my_index < (total_devices - 1):
        _downstream_mac = mac_to_bytes(device_list[my_index + 1].get('mac'))
    else:
        is_endpoint = True

    # 5. log resolved neighbor names and device operational role
    upstream_name = "None"
    downstream_name = "None"
    if my_index > 0:
        upstream_name = device_list[my_index - 1].get('name')
    if my_index < (total_devices - 1):
        downstream_name = device_list[my_index + 1].get('name')
    # determine role label for console output
    if my_index == 0:

        from push_button import PushButton

        button = PushButton(5, send_message)
        role_label = "INITIATOR"
    elif is_endpoint:
        role_label = "ENDPOINT"
    else:
        role_label = "RELAY NODE"
    log.info("topology routing resolved:")
    log.info("  ├─ Role:       {}".format(role_label))
    log.info("  ├─ Upstream:   {}".format(upstream_name))
    log.info("  └─ Downstream: {}".format(downstream_name))

    # 5. initialize the Relay instance with injected factory and routing maps
    _relay_node = Relay(
        message_factory=_message_factory,
        pixel=pixel,
        upstream_mac=_upstream_mac,
        downstream_mac=_downstream_mac,
        is_endpoint=is_endpoint
    )

    # 7. execution processing via asyncio
    log.info("scheduling relay engine task and starting event loop.")
    # schedule the relay node background worker
    asyncio.create_task(_relay_node.run_loop())
    # schedule MessageBus background tasks here as well
    # asyncio.create_task(message_bus.start())
    # keep the main thread alive or run the main loop hook
    asyncio.get_event_loop().run_forever()

except KeyboardInterrupt:
    log.info('interrupted.')
except Exception as e:
    log.error('{} raised: {}'.format(type(e), e))
    sys.print_exception(e)
finally:
    pixel.close()

#EOF
