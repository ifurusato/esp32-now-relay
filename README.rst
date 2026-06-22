*******************************************************
esp32-now-replay: A multi-node relay based on ESP32-NOW
*******************************************************

This provides a means of interconnecting a configured relay of ESP32
evices via ESP32-NOW, so that messages may be sent back and forth 
across the relay.


Features
--------

* provides a script to obtain the MAC address of a device
* YAML configuration
* each device determines its own placement in the relay


Installation
------------

First, install the software on all devices. These must be ESP32 versions
that support ESP32-NOW.

Execute get_mac.py on each device to determine its MAC address.

Edit the config.yaml file to contain the number of devices, including the
MAC address of each. The first device in the list is the initiator node,
the last is the endpoint node, and the rest are relay nodes. Copy the
properly configured config.yaml file to each of the nodes.


Requirements
------------

This has been tested on MicroPython v1.25.0 and should work on any newer
versions.


Files
-----

* yaml.py:              The YAML parser
* config_loader.py:     A convenient application configuration loader
* config.yaml:          YAML configuration file (must be modified)
* ...


Status
******

This is a first release and supports the features as described, but it has not
been extensively tested.


Support & Liability
*******************

This project comes with no promise of support or acceptance of liability. Use at
your own risk.


Copyright & License
*******************

All contents Copyright 2026 by Ichiro Furusato. All rights reserved.

Software and documentation are distributed under the MIT License, see LICENSE
file included with project.

