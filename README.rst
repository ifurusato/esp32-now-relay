*******************************************************
esp32-now-replay: A multi-node relay based on ESP32-NOW
*******************************************************

This provides a means of interconnecting a configured relay of ESP32
devices via ESP32-NOW, so that messages may be sent back and forth 
across the relay.


Features
--------

* provides a script to obtain the MAC address of a device
* uses a YAML configuration for device name, MAC address and enabled/disabled state
* each device determines its own placement in the relay
* messages passed contain a UUID, payload and age marker


Future Work
-----------

* Integrate Relay into existing asyncio MessageBus architecture so that each 
  Relay node becomes part of a network-distributed pub-sub system. Publishers 
  and Subscribers will be able to utilise the Relay for message passing between
  nodes.


Installation
------------

First, install the software on all devices. These must be ESP32 versions
that support ESP32-NOW.


Configuration
-------------

Execute identify.py on each device to determine its MAC address and machine
identifier.

Edit the config.yaml file to contain the number of devices, including the
MAC address of each. The 'name' value is anything that is helpful to identify
the device amongst others. 

The first device in the list is the initiator node, the last is the endpoint 
node, and the rest are relay nodes. Copy the properly configured config.yaml 
file to each of the nodes.

If there is no corresponding machine identifier in main.py, no RGB LED pixel
class will be assigned, and there will be no visual indication of activity.


Usage
-----

Once the files and configuration are complete, all the devices should be
reset. Each will start with three light blue flashes followed by a steady
blue. This indicates the Relay is ready. A pushbutton connected between
IO5 and ground of the initiator node will trigger a message onto the bus.

The message will travel to the endpoint, be processed and return to the 
initiator node. The LEDs on all devices will change color momentarily to 
indicate status. The message is reversed by the endpoint node, so the
value as returned will reflect that change.


Requirements
------------

This has been tested with MicroPython v1.25.0 and v1.28.0 and should work 
on any newer version.

This should work on all ESP32 boards that support ESP32-NOW, including
but not limited to ESP32-DOWD, ESP32-S2, ESP32-S3, ESP32-C2/C3/C6/H2.

This has so far been successfully tested on:

* Unexpected Maker TinyPICO
* Unexpected Maker TinyS3
* Unexpected Maker Feather S2
* Waveshare ESP32-S3 Zero

The only real issue in implementing for a new board is support for the RGB LED,
which comes down to whether it's a NeoPixel (WS2812B) or a Dotstar (APA102. A
new wrapper class is created for the device and main.py modified to handle it.


Files
-----

See FILES for a list and description of project files.


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

