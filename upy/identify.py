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

import sys
import network
import ubinascii

# initialize station interface to activate radio
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# retrieve hardware MAC address
mac_bytes = wlan.config('mac')
# format into a readable hex string format
mac_hex = ubinascii.hexlify(mac_bytes, ':').decode('utf-8')
print("MAC address:          {}".format(mac_hex))

# obtain machine identifier
machine_info = sys.implementation._machine.lower()
print("device identifier:   '{}'".format(machine_info))

#EOF
