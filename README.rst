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


Encryption
----------

There is an option to send messages using ESP32-NOW encryption. 

This uses the config.yaml file that's been populated with the MAC addresses 
of the relay nodes along with a new key_generator.py script, which generates 
a global PMK key and a set of LMK keys, one for each node pairing, which is 
stored in a keys.yaml file. Enabling encryption in config.yaml then uses this 
file to set up encrypted transport between nodes.

To generate the keys.yaml file, enter the REPL::

    MicroPython v1.25.0 on 2025-04-15; FeatherS2 with ESP32-S2
    Type "help()" for more information.
    >>>
    >>> from key_generator import KeyGenerator
    >>> KeyGenerator.generate_keys()
    2026-06-25T21:17:29.591Z : key-gen        : INFO  : loading configuration…
    2026-06-25T21:17:29.671Z : key-gen        : INFO  : loaded configuration for 3 devices.
    2026-06-25T21:17:29.677Z : key-gen        : INFO  : generated key for device with MAC address: dc:54:75:eb:69:c8
    2026-06-25T21:17:29.682Z : key-gen        : INFO  : generated key for device with MAC address: 64:b7:08:90:5c:c4
    2026-06-25T21:17:29.687Z : key-gen        : INFO  : generated key for device with MAC address: 50:78:7d:17:fe:d8
    2026-06-25T21:17:29.713Z : key-gen        : INFO  : generated global key.
    2026-06-25T21:17:29.719Z : key-gen        : INFO  : writing output to: keys.yaml
    2026-06-25T21:17:30.777Z : key-gen        : INFO  : complete.
    True
    >>>

The keys.yaml file must then be copied across all nodes in the relay.


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

