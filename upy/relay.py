#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-22
# modified: 2026-06-23

import sys
import asyncio
import time
import ubinascii

from colorama import Fore, Style
from colors import *
from event import *
from component import Component
from logger import Logger, Level
from config_error import ConfigurationError
from message_codec import MessageCodec

class Relay(Component):
    NAME = 'relay'

    def __init__(self, config=None, networking=None, message_bus=None, message_factory=None, pixel=None, level=Level.INFO):
        '''
        Initializes network interfaces and injects the centralized message factory.
        '''
        Component.__init__(self, Relay.NAME, suppressed=False, enabled=False, level=level)
        self._config          = config
        self._networking      = networking
        self._message_bus     = message_bus
        self._message_factory = message_factory
        self._message_codec   = MessageCodec(message_factory, level)
        self._pixel = pixel
        # load device list from configuration ┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        _cfg = self._config['relay']
        self._verbose = _cfg['verbose']
        self._device_list = _cfg['devices']
        self._total_devices = len(self._device_list)
        self._log.info('loaded configuration for ' + Fore.GREEN + '{} devices:'.format(self._total_devices))
        self._local_mac_str = self._networking.mac_address
        self.print_configuration()
        self._log.info('device MAC address: ' + Fore.GREEN + '{}'.format(self._local_mac_str))
#       # find this device's position in catalog ┈┈┈┈┈┈┈┈┈┈┈
        self._index, local_device = Relay.find_device_by_mac(self._device_list, self._local_mac_str)
        if self._index is None:
            self._show_color(COLOR_RED)
            raise ConfigurationError("local MAC address '{}' not found in topology catalog.".format(self._local_mac_str))
        else:
            self._show_color(COLOR_DEEP_CYAN)
            self._log.info('this device identified as: '
                    + Fore.GREEN + '{}'.format(self._device_list[self._index].get('name')))
        # set up ESP32-NOW ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._espnow = self._networking.espnow
        self._rx_callback    = None
        self._led_task       = None
        # set up encryption ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._encryption_enabled = False
        if _cfg['encryption' ] is True:
            self._load_encryption_keys()
        else:
            self._log.info('using open transport.')
        # configure relay routing map ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._upstream_name        = None
        self._downstream_name      = None
        self._upstream_mac_bytes   = None
        self._downstream_mac_bytes = None
        self._upstream_mac         = None # human-readable MAC address
        self._downstream_mac       = None # human-readable MAC address
        self._is_endpoint          = False
        self._seen_errors          = []
        _enabled = self._build_routing_map()
        if not _enabled:
            self.disable()
        # if this is first node, set up Initiator ┈┈┈┈┈┈┈┈┈┈
        self._initiator = None
        if self._index == 0:
            self._establish_initiator()
        if self.enabled:
            self._log.info('ready.')
        else:
            self._log.info('ready in disabled state.')

    @property
    def index(self):
        '''
        Return the index number of this device within the relay.
        '''
        return self._index

    @property
    def upstream_mac(self):
        '''
        Return the MAC address of the upstream device in the relay as a human-readable string.

        This can be converted to a bytes object via mac_to_bytes().
        '''
        return self._upstream_mac

    @property
    def upstream_mac_bytes(self):
        '''
        Return the MAC address of the upstream device in the relay.
        '''
        return self._upstream_mac_bytes

    @property
    def downstream_mac(self):
        '''
        Return the MAC address of the downstream device in the relay as a human-readable string.

        This can be converted to a bytes object via mac_to_bytes().
        '''
        return self._downstream_mac

    @property
    def downstream_mac_bytes(self):
        '''
        Return the MAC address of the downstream device in the relay.
        '''
        return self._downstream_mac_bytes

    def enable(self):
        '''
        Enable the relay by scheduling its execution loop.
        '''
        if self.closed:
            self._log.warn('already closed.')
        elif not self.enabled:
            self._log.info('enabling relay node…')
            super().enable()
            asyncio.create_task(self._run_loop())
            self._log.info(Fore.GREEN + 'relay ready.')
        else:
            self._log.warn('already enabled.')

    def _load_encryption_keys(self):
        '''
        Attempt to load keys.yaml, which contains the PMK and LMK keys. If this fails it disables encryption.
        '''
        self._log.info('attempting to enable encrypted transport…')
        
        from yaml import FileNotFoundError
        from config_loader import ConfigLoader

        keys_filename = 'keys.yaml'
        try:
            keys_config = ConfigLoader.configure(keys_filename, suppress_error_message=True)
            # configure global PMK
            global_pmk_hex = keys_config['relay']['pmk']
            self._espnow.set_pmk(bytes.fromhex(global_pmk_hex))
            # cache the device keys map
            self._crypto_peers = keys_config['relay']['devices']
            self._encryption_enabled = True
            self._log.info('successfully loaded keys configuration: ' + Fore.GREEN + "encryption enabled.")
        except ( FileNotFoundError, OSError) as e:
            # file does not exist or cannot be read
            self._log.warn("cannot enable encryption: '{}' file not found.\n{:>52}".format(keys_filename, '')
                    + 'Generate it via key_generator.py and share across all nodes.')
            self._encryption_enabled = False
            self._log.info(Fore.WHITE + Style.BRIGHT + 'using open transport.')
        except Exception as e:
            self._log.error('cannot enable encryption: {} raised reading {} file: {}'.format(type(e), keys_filename, e))
            self._encryption_enabled = False
            self._log.info(Fore.WHITE + Style.BRIGHT + 'using open transport.')

    def print_configuration(self):
        for i, device in enumerate(self._device_list):
            num = i + 1
            name = device.get('name')
            mac_address = device.get('mac')
            enabled = device.get('enabled')
            if not enabled:
                self._log.info(Style.DIM 
                        + '[{}]  {:<34} '.format(num, name) 
                        + 'mac: ' + Fore.GREEN + '{}'.format(mac_address))
            elif mac_address == self._local_mac_str.lower():
                self._log.info('[{}]  {:<34} '.format(num, name) + Style.BRIGHT
                        + 'mac: ' + Fore.GREEN + '{}'.format(mac_address))
            else:
                self._log.info('[{}]  {:<34} '.format(num, name) 
                        + 'mac: ' + Fore.GREEN + '{}'.format(mac_address))

    def _establish_initiator(self):
        '''
        Set up push button to trigger messages.
        '''
        self._log.info("establishing initiator…")

        from initiator import Initiator

        self._initiator = Initiator(self._config, self)


    def _add_neighbor_peer(self, label, mac_str, mac_bytes):
        '''
        Registers a single neighbor peer with encryption if enabled. This adds the key for
        each node pairing so the same key is used for transmissions in both directions.

        :param label:       either 'upstream' or 'downstream' to indicate which node
        :param mac_str:      the human-readable MAC address
        :param mac_bytes:    the MAC address in bytes
        '''
        if self._encryption_enabled:
            this_device = self._device_list[self._index]
            this_mac_str = this_device.get('mac')
            # determine the link key by using the lower index node's MAC address
            if label == 'upstream':
                # upstream neighbor has a lower index than this node
                link_mac_str = mac_str
            else:
                # this node has a lower index than the downstream neighbor
                link_mac_str = this_mac_str
            lmk_hex = self._crypto_peers.get(link_mac_str)
            if lmk_hex:
                self._log.info("setting LMK for pair: {}{}{} 🡰 🡲  {}{}{}".format(
                        Fore.GREEN,
                        this_mac_str, 
                        Fore.CYAN,
                        Fore.GREEN,
                        mac_str,
                        Fore.CYAN))
                self._log.info('adding encrypted {:>10} peer        mac: '.format(label) + Fore.GREEN + '{}'.format(mac_str))
                self._espnow.add_peer(mac_bytes, bytes.fromhex(lmk_hex), encrypt=True) 
                mac_bytes, lmk_bytes, channel, ifidx, encrypt = self._espnow.get_peer(mac_bytes)
                mac = self.bytes_to_mac(mac_bytes)
                lmk = self.bytes_to_lmk(lmk_bytes)
                self._log.debug('info: ' + Fore.BLUE + "mac: '{}'; lmk: '{}'; channel: {}; ifidx: {}; encrypt: {}".format(mac, lmk, channel, ifidx, encrypt))
            else:
                self._log.warn("no LMK found for link key {}; registering unencrypted.".format(link_mac_str))
                self._espnow.add_peer(mac_bytes)
        else:   
            self._espnow.add_peer(mac_bytes)

    def _build_routing_map(self):
        '''
        Build neighbor routing maps and display to console.
        Returns a flag indicating whether this device is enabled or disabled.
        '''
        # scan backwards to find the first enabled upstream neighbor
        for i in range(self._index - 1, -1, -1):
            device = self._device_list[i]
            if device.get('enabled', True):
                self._upstream_name = device.get('name')
                self._upstream_mac = device.get('mac')
                self._upstream_mac_bytes = self.mac_to_bytes(self._upstream_mac)
                self._log.debug("upstream name: '{}'; mac='{}'".format(self._upstream_name, self._upstream_mac))
                self._add_neighbor_peer("upstream", self._upstream_mac, self._upstream_mac_bytes)
                break
        # scan forwards to find the first enabled downstream neighbor
        for i in range(self._index + 1, self._total_devices):
            device = self._device_list[i]
            if device.get('enabled', True):
                self._downstream_name = device.get('name')
                self._downstream_mac = device.get('mac')
                self._downstream_mac_bytes = self.mac_to_bytes(self._downstream_mac)
                self._log.debug("downstream name: '{}'; mac='{}'".format(self._downstream_name, self._downstream_mac))
                self._add_neighbor_peer("downstream", self._downstream_mac, self._downstream_mac_bytes)
                break
        else:
            self._is_endpoint = True
        # determine role label for console output
        _enabled = self._device_list[self._index].get('enabled');
        if not _enabled:
            role_label = Fore.RED + "DISABLED"
            # disable device if configuration flag is False
        elif self._index == 0:
            role_label = Fore.GREEN + "INITIATOR"
        elif self._is_endpoint:
            role_label = Fore.GREEN + "ENDPOINT"
        else:
            role_label = Fore.GREEN + "RELAY NODE"
        self._log.info("topology routing resolved:")
        self._log.info("  ├─ Role:       {}".format(role_label))
        self._log.info("  ├─ Upstream:   {}{}".format(Fore.GREEN, self._upstream_name))
        self._log.info("  └─ Downstream: {}{}".format(Fore.GREEN, self._downstream_name))
        return _enabled

    def set_receive_callback(self, callback):
        self._rx_callback = callback

    def send_message(self, peer, direction, message):
        '''
        Serializes an existing Message instance and transmits it over the network.
        '''
        if not isinstance(peer, bytes):
            raise TypeError('was passed {} rather than bytes object.'.format(type(peer)))
        if self._verbose:
            self._log.info('sending message in {} direction: {}'.format(direction, message))
        payload = self._message_codec.serialize(direction, message)
        ok = False
        try:
            encoded_payload = payload.encode('utf-8')
            payload_len = len(encoded_payload)
            self._log.debug('sending message in direction: {}.'.format(direction))
            ok = self._espnow.send(peer, encoded_payload)
            self._log.info("ok type: {}; value: '{}'".format(type(ok), ok))
            if not ok:
                if peer == self._upstream_mac_bytes:
                    self._log.error("error sending message to upstream peer '{}': {}".format(self._upstream_name, self._upstream_mac))
                    # not recoverable as we can't get back to initiator
                elif peer == self._downstream_mac_bytes:
                    self._log.error("error sending message to downstream peer '{}': {}".format(self._downstream_name, self._downstream_mac))
                    # send error message back to initiator
                    self._handle_routing_failure(message)

        except Exception as e:
            self._log.error("{} raised sending message to peer: '{}': {}".format(type(e), peer, e))
            sys.print_exception(e)
        finally:
            if ok:
                self._log.debug('message was sent.')
            else:
                self._log.warn('message was not sent.')

    def _handle_routing_failure(self, message):
        '''
        Handles downstream transport failure by bouncing the message upstream
        with an inverted direction flag, protected against infinite routing loops.
        '''
        self._log.info('handling routing error…')
        if message.id in self._seen_errors:
            self._log.warning("routing loop detected for message id: '{}'; dropping packet.".format(message.id))
            return
        # track the error and manage bounded cache constraint
        self._seen_errors.append(message.id)
        if len(self._seen_errors) > 20:
            self._seen_errors.pop(0)
        _value = "DELIVERY FAILURE: id={}; event={}; downstream peer: {}; MAC={}".format(
                message.id, 
                message.event.label, 
                self._downstream_name, 
                self._downstream_mac)
        self._log.info('sending error message to initiator: ' + Fore.YELLOW + '{}'.format(_value))
        _error_message = self._message_factory.create_message(event=FAILURE, value=_value)
        _error_message.id = message.id # error message shares ID with original
        self.send_message(self._upstream_mac_bytes, -1, _error_message)

    def process_endpoint_logic(self, incoming_message):
        '''
        Executes operations on the last Node and requests a new message from the factory.
        '''
        _value = incoming_message.value
        if self._verbose:
            self._log.info('processing endpoint logic for message: '
                    + Fore.GREEN + '{}'.format(incoming_message))
        else:
            self._log.info('inbound message: ' + Fore.GREEN + '{}'.format(_value))
        # reverse string
        response_value = self._reverse_string(_value)
        # or prepend 'processed' to string
#       response_value = "processed: {}".format(_value)
        self._log.info('outbound message: ' + Fore.GREEN + '{}'.format(response_value))
        return self._message_factory.create_message(
            event=RELAY,
            value=response_value
        )

    def handle_outbound(self, message):
        '''
        Handles messages moving down the chain toward the endpoint (Node 5).
        '''
        if self._led_task:
            self._led_task.cancel()
        if self._is_endpoint:
            if self._verbose:
                self._log.info('handling outbound message at endpoint: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_TANGERINE, 3000))
            response_msg = self.process_endpoint_logic(message)
            if self._upstream_mac_bytes:
                self.send_message(self._upstream_mac_bytes, -1, response_msg)
        else:
            if self._verbose:
                self._log.info('handling outbound message: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_SKY_BLUE, 500))
            if self._downstream_mac_bytes:
                self.send_message(self._downstream_mac_bytes, 1, message)

    def handle_inbound(self, message):
        '''
        Handles messages moving up the chain back toward the initiator (Node 1).
        '''
        if self._upstream_mac_bytes:
            if self._verbose:
                self._log.info('handling inbound message: {}'.format(message))
            self._led_task = asyncio.create_task(self._flash_led(COLOR_DEEP_FUCHSIA, 500))
            self.send_message(self._upstream_mac_bytes, -1, message)
        else:
            if self._verbose:
                self._log.info("initiator received ricochet response: {}".format(repr(message)))
            if self._rx_callback:
                self._rx_callback(message)
            self._led_task = asyncio.create_task(self._flash_led(COLOR_APPLE, 3000))

    async def _run_loop(self):
        '''
        Asynchronous polling loop that processes incoming packets without blocking.
        '''
        while True:
            # check for incoming ESP-NOW packets
            host, msg = self._espnow.recv()
            if msg is not None:
                self._log.info("received message: '{}'".format(msg))
                try:
                    decoded_msg = msg.decode('utf-8')
#                   self._log.debug("decoded message: '{}'".format(decoded_msg))
                    direction, reconstructed_msg = self._message_codec.deserialize(decoded_msg)
#                   self._log.debug("reconstructed message: '{}'".format(reconstructed_msg))
                    if direction == 1:
                        self.handle_outbound(reconstructed_msg)
                    elif direction == -1:
                        self.handle_inbound(reconstructed_msg)
                except Exception as e:
                    self._log.error('error in relay: {}'.format(e))
            # yield control back to the asyncio scheduler
            await asyncio.sleep_ms(5)

    # utility methods ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    @staticmethod
    def find_device_by_mac(device_list, mac_str):
        '''
        Searches a list of device configurations for a matching MAC address.
        
        :param device_list: The list of device dictionaries from config
        :param mac_str: The target MAC address string
        :return: A tuple of (index, device_dict) if found, otherwise (None, None)
        '''
        target_mac = mac_str.strip().lower()
        for i, device in enumerate(device_list):
            # Enforce direct lookup logic
            if device['mac'].strip().lower() == target_mac:
                return i, device
        return None, None

    def _show_color(self, color):
        '''
        Set the color of the pixel.
        '''
        if self._pixel:
            self._pixel.show_color(color)

    async def _flash_led(self, color, duration_ms=1000):
        self._log.debug('flash led: {}'.format(color.name))
        self._show_color(color)
        await asyncio.sleep_ms(duration_ms)
        self._show_color(COLOR_BLACK)

    def _reverse_string(self, value):
        '''
        Reverse the characters in the argument.
        '''
        return ''.join(reversed(value))

    def mac_to_bytes(self, mac_str):
        '''
        Converts a colon-separated hex MAC string into a bytes object.
        '''
        clean_hex = mac_str.replace(':', '')
        return ubinascii.unhexlify(clean_hex)

    def bytes_to_mac(self, mac_bytes):
        '''
        Converts a bytes object into a colon-separated hex MAC string.
        '''
        hex_str = ubinascii.hexlify(mac_bytes).decode('utf-8')
        return ':'.join([hex_str[i:i+2] for i in range(0, 12, 2)])

    def bytes_to_lmk(self, lmk_bytes):
        '''
        Converts a bytes object into a standard hex string representation.
        '''
        return ubinascii.hexlify(lmk_bytes).decode('utf-8')

#EOF
