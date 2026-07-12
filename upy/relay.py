#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-22
# modified: 2026-07-12
#
# ESP-NOW RELAY

import sys
import asyncio
import time
import ubinascii

from colorama import Fore, Style
from colors import *
from event import *
from direction import *
from logger import Logger, Level
from component import Component
from component_registry import ComponentRegistry
from config_error import ConfigurationError
from message_codec import MessageCodec

class Relay(Component):
    NAME = 'relay'
    '''
    A network relay connecting a series of ESP-NOW nodes.

    From existing networking sets up inbound and outbound peers, with or without encryption.
    '''
    def __init__(self, config=None, networking=None, message_factory=None, pixel=None, level=Level.INFO):
        Component.__init__(self, Relay.NAME, suppressed=False, enabled=False, level=level)
        self._config          = config
        self._networking      = networking
        self._message_codec   = MessageCodec(message_factory, level)
        self._pixel = pixel
        # load device list from configuration ┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        _cfg = self._config['rros']['relay']
        self._verbose       = _cfg['verbose']
        self._device_list   = _cfg['devices']
        self._enable_pixel  = _cfg['enable_pixel'] and pixel is not None
        self._total_devices = len(self._device_list)
        self._local_mac_str = self._networking.mac_address
        self._log.info('device MAC address: ' + Fore.GREEN + '{}'.format(self._local_mac_str))
        # find this device's position in catalog ┈┈┈┈┈┈┈┈┈┈┈
        self._index, local_device = Relay.find_device_by_mac(self._device_list, self._local_mac_str)
        if self._index is None:
            if self._enable_pixel:
                self._show_color(COLOR_RED)
            raise ConfigurationError("local MAC address '{}' not found in topology catalog.".format(self._local_mac_str))
        else:
            if self._enable_pixel:
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
        # display relay configuration ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        _missing = self._print_configuration()
        # configure relay routing map ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
        self._inbound_name        = None
        self._outbound_name       = None
        self._inbound_mac_bytes   = None
        self._outbound_mac_bytes  = None
        self._inbound_mac_str     = None # human-readable MAC address
        self._outbound_mac_str    = None # human-readable MAC address
        self._is_initiator        = False
        self._is_endpoint         = False
        self._seen_errors         = []
        _enabled = self._build_routing_map()
        if self._is_endpoint and self._inbound_mac_bytes is None:
            self._log.warn('endpoint error: index={}; inbound: {}; outbound: {}'.format(self._index, self._inbound_mac_bytes, self._outbound_mac_bytes ))
        if self._is_initiator and self._outbound_mac_bytes is None:
            self._log.warn('initiator error: index={}; inbound: {}; outbound: {}'.format(self._index, self._inbound_mac_bytes, self._outbound_mac_bytes ))
        else:
            self._log.debug('configured: index={}; inbound: {}; outbound: {}'.format(self._index, self._inbound_mac_bytes, self._outbound_mac_bytes ))
        if _missing > 0:
            self._log.warn('{} missing node(s) in relay.'.format(_missing))
        if not _enabled:
            self.disable()
        if self.enabled:
            self._log.info('ready.')
        else:
            self._log.info('ready in disabled state.')

    def set_gateway(self, gateway):
        self._gateway = gateway

    def is_initiator(self):
        '''
        Return true if this node is the initiator, the first node in the relay.
        '''
        return self._is_initiator

    def is_endpoint(self):
        '''
        Return true if this node is the endpoint, the last node in the relay.
        '''
        return self._is_endpoint

    @property
    def index(self):
        '''
        Return the index number of this device within the relay.
        Note that this is 0-based, i.e., node 1's index is 0.
        '''
        return self._index

    @property
    def inbound_mac(self):
        '''
        Return the MAC address of the inbound device in the relay as a human-readable string.
        This can be converted to a bytes object via mac_to_bytes().
        '''
        return self._inbound_mac_str

    @property
    def inbound_mac_bytes(self):
        '''
        Return the MAC address of the inbound device in the relay.
        '''
        return self._inbound_mac_bytes

    @property
    def outbound_mac(self):
        '''
        Return the MAC address of the outbound device in the relay as a human-readable string.
        This can be converted to a bytes object via mac_to_bytes().
        '''
        return self._outbound_mac_str

    @property
    def outbound_mac_bytes(self):
        '''
        Return the MAC address of the outbound device in the relay.
        '''
        return self._outbound_mac_bytes

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

    def set_receive_callback(self, callback):
        self._rx_callback = callback

    def send_message(self, peer, direction, message):
        '''
        Serialises an existing Message instance and transmits it over the network.
        '''
        if not isinstance(peer, bytes):
            raise TypeError('was passed {} rather than bytes object.'.format(type(peer)))
        if not isinstance(direction, Direction):
            raise TypeError('was passed {} rather than Direction object.'.format(type(direction)))
        if self._verbose:
            self._log.info('sending message {}: {}'.format(direction.name, message))
        payload = self._message_codec.serialise(direction, message)
        ok = False
        try:
            encoded_payload = payload.encode('utf-8')
            payload_len = len(encoded_payload)
            if self._verbose:
                self._log.info('sending message {}.'.format(direction.name))
            ok = self._espnow.send(peer, encoded_payload)
            if ok:
                self._log.debug('message was sent.')
            else:
                self._log.warn('message was not sent.')
                if peer == self._inbound_mac_bytes:
                    self._log.error("error sending message to inbound peer '{}': {}".format(self._inbound_name, self._inbound_mac_str))
                    # not recoverable as we can't get back to initiator
                elif peer == self._outbound_mac_bytes:
                    # send error message back to initiator
                    self._handle_routing_failure(message)
        except Exception as e:
            self._log.error("{} raised sending message to peer: '{}': {}".format(type(e), peer, e))
            sys.print_exception(e)

    def _process_endpoint_logic(self, message):
        '''
        Executes any operations when on the endpoint Node and then returns the
        message to the outbound handler.
        '''
        if message.event == RTC:
            # disable further relay passage of message
            message.tnid == None
        if self._verbose:
            self._log.info('processed endpoint logic for message: ' + Fore.GREEN + '{}'.format(message))
        return message

    def _handle_outbound(self, message):
        '''
        Handles messages moving down the chain toward the endpoint (the last
        node in the sequence).

        If at the endpoint we create a clone of the Message to be passed to the
        Gateway, which is passed to the local MessageBus before returning to
        the Relay.
        '''
        if self._led_task:
            self._led_task.cancel()
        _direction = INBOUND if self._is_endpoint else OUTBOUND
        _note = ''
        _color = ''
        if self._is_initiator:
            _color = Fore.WHITE
            _note = 'at initiator'
        elif self._is_endpoint:
            _color = Fore.GREEN
            _note = 'at endpoint'
            message = self._process_endpoint_logic(message)
        else:
            _color = Fore.BLUE
            _note = 'in transit'
        if self._verbose:
            self._log.info('handling outbound message {}{}:{} {}'.format(_color, _note, Fore.GREEN, message))

        # we pass the message to the gateway
        self._gateway.receive_from_relay(message)
        if self._enable_pixel:
            self._led_task = asyncio.create_task(self._flash_led(COLOR_DEEP_FUCHSIA, 3000))

    def _handle_inbound(self, message):
        '''
        Handles messages moving up the chain back toward the initiator (Node 1).

        Messages in this reverse direction are never intercepted by the local MessageBus
        as their intended purpose is acknowledgement to the initiator.
        '''
        if self._inbound_mac_bytes:
            if self._verbose:
                self._log.info('handling inbound message: {}'.format(message))
            if self._enable_pixel:
                self._led_task = asyncio.create_task(self._flash_led(COLOR_APPLE, 500))
            self.send_message(self._inbound_mac_bytes, INBOUND, message)
        else:
            if self._verbose:
                self._log.info("initiator received ricochet response: {}".format(repr(message)))
            if self._rx_callback:
                self._rx_callback(message)
            if self._enable_pixel:
                self._led_task = asyncio.create_task(self._flash_led(COLOR_EMERALD, 3000))

    async def _run_loop(self):
        '''
        Asynchronous polling loop that processes incoming packets without blocking.
        '''
        while True:
            # check for incoming ESP-NOW packets
            host, encoded_message = self._espnow.recv()
            if encoded_message is not None:
#               self._log.debug("received message: '{}'".format(encoded_message))
                try:
                    if encoded_message == b'\x00':
                        continue
                    decoded_msg = encoded_message.decode('utf-8')
#                   self._log.debug("decoded message: '{!r}' ({} chars)".format(decoded_msg, len(decoded_msg)))
                    if len(decoded_msg) > 0:
                        direction, reconstructed_msg = self._message_codec.deserialise(decoded_msg)
#                       self._log.debug("reconstructed message: '{}'".format(reconstructed_msg))
                        if direction is OUTBOUND:
                            self._handle_outbound(reconstructed_msg)
                        elif direction is INBOUND:
                            self._handle_inbound(reconstructed_msg)
                    else:
                        self._log.warning("empty message.")
                except Exception as e:
                    self._log.error('error in relay: {}'.format(e))
                    sys.print_exception(e)
            # yield control back to the asyncio scheduler
            await asyncio.sleep_ms(5)

    # configuration ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

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

    def _add_neighbor_peer(self, direction, mac_bytes, mac_str):
        '''
        Registers a single neighbor peer with encryption if enabled. This adds the key for
        each node pairing so the same key is used for transmissions in both directions.

        :param direction:    either OUTBOUND or INBOUND
        :param mac_bytes:    the MAC address in bytes
        :param mac_str:      the human-readable MAC address
        '''
        if not isinstance(direction, Direction):
            raise TypeError('expected direction argument.')
        if self._encryption_enabled:
            this_device = self._device_list[self._index]
            this_mac_str = this_device.get('mac')
            # determine the link key by using the lower index node's MAC address
            if direction is INBOUND:
                # inbound neighbor has a lower index than this node
                link_mac_str = mac_str
            else:
                # this node has a lower index than the outbound neighbor
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
                self._log.info('adding encrypted {:>10} peer        mac: '.format(direction.name) + Fore.GREEN + '{}'.format(mac_str))
                self._add_peer(mac_bytes, mac_str, bytes.fromhex(lmk_hex), encrypt=True) 
                mac_bytes, lmk_bytes, channel, ifidx, encrypt = self._espnow.get_peer(mac_bytes)
                mac = self.bytes_to_mac(mac_bytes)
                lmk = self.bytes_to_lmk(lmk_bytes)
#               self._log.debug('info: ' + Fore.BLUE + "mac: '{}'; lmk: '{}'; channel: {}; ifidx: {}; encrypt: {}".format(mac, lmk, channel, ifidx, encrypt))
            else:
                self._log.warn("no LMK found for link key {}; registering unencrypted.".format(link_mac_str))
                self._add_peer(mac_bytes, mac_str)
        else:   
            self._add_peer(mac_bytes, mac_str)

    def _add_peer(self, mac_bytes, mac_str, lmk=None, encrypt=False):
        '''
        Adds the MAC address as a peer. If lmk is supplied and encrypt is True we assume this is an encrypted peer.
        This wraps the method with a try-except block since this can fail in various ways.
        '''
        try:
            if lmk and encrypt:
                self._espnow.add_peer(mac_bytes, lmk, encrypt=encrypt) 
            else:
                self._espnow.add_peer(mac_bytes)
        except OSError as e:
            if e.args and e.args[0] == -12395: # ESP_ERR_ESPNOW_EXIST
                self._log.warn('peer {} already exists.'.format(mac_str))
            else:
                self._log.error('error adding peer {}: {}'.format(mac_str, e))
                raise # handle any other OSErrors

    def _build_routing_map(self):
        '''
        Build neighbor routing maps and display to console.

        This assigns boolean values to _is_initiator and _is_endpoint flags.

        Returns a flag indicating whether this device is enabled or disabled.
        '''
        # scan backwards to find the first enabled inbound neighbor
        for i in range(self._index - 1, -1, -1):
            device = self._device_list[i]
            if device.get('enabled', True):
                self._inbound_name = device.get('name')
                self._inbound_mac_str = device.get('mac')
                self._inbound_mac_bytes = self.mac_to_bytes(self._inbound_mac_str)
#               self._log.debug("inbound name: '{}'; mac='{}'".format(self._inbound_name, self._inbound_mac_str))
                self._add_neighbor_peer(INBOUND, self._inbound_mac_bytes, self._inbound_mac_str)
                break
        # scan forwards to find the first enabled outbound neighbor
        for i in range(self._index + 1, self._total_devices):
            device = self._device_list[i]
            if device.get('enabled', True):
                self._outbound_name = device.get('name')
                self._outbound_mac_str = device.get('mac')
                self._outbound_mac_bytes = self.mac_to_bytes(self._outbound_mac_str)
#               self._log.debug("outbound name: '{}'; mac='{}'".format(self._outbound_name, self._outbound_mac_str))
                self._add_neighbor_peer(OUTBOUND, self._outbound_mac_bytes, self._outbound_mac_str)
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
            self._is_initiator = True
        elif self._is_endpoint:
            role_label = Fore.GREEN + "ENDPOINT"
        else:
            role_label = Fore.GREEN + "RELAY NODE"
        self._log.info("topology routing resolved:")
        self._log.info("  ├─ Role:       {}".format(role_label))
        self._log.info("  ├─ Upstream:   {}{}".format(Fore.GREEN, self._inbound_name))
        self._log.info("  └─ Downstream: {}{}".format(Fore.GREEN, self._outbound_name))
        return _enabled

    # utility methods ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

    def _handle_routing_failure(self, message):
        '''
        Handles outbound transport failure by bouncing the message inbound
        with an inverted direction, protected against infinite routing loops.
        '''
        self._log.info('handling routing error…')
        if message.id in self._seen_errors:
            self._log.warning("routing loop detected for message id: '{}'; dropping packet.".format(message.id))
            return
        # track the error and manage bounded cache constraint
        self._seen_errors.append(message.id)
        if len(self._seen_errors) > 20:
            self._seen_errors.pop(0)
        _value = "sending message to outbound peer '{}' at MAC: {}'{}'\n{}{}".format(
                self._outbound_name, 
                Fore.GREEN,
                self._outbound_mac_str,
                Fore.CYAN + Style.DIM,
                message
            )
        if self._is_initiator:
            self._log.error('routing error: {}'.format(_value))
            if self._enable_pixel:
                self._show_color(COLOR_RED)
        else:
            self._log.info('sending error message to initiator: ' + Fore.YELLOW + '{}'.format(_value))
            message.event = FAILURE
            self.send_message(self._inbound_mac_bytes, INBOUND, message)

    def _print_configuration(self):
        '''
        Prints the current network relay configuration to the console.
        This does have a diagnostic result, returning the count of missing
        nodes, if any of the required (enabled) nodes are not in range and
        therefore not available.
        '''
        self._log.info('loaded configuration for ' + Fore.GREEN + '{} devices:'.format(self._total_devices))
        _missing = 0
        inboard_peer, outboard_peer = self._get_active_peers(self._index)
        inboard_id  = inboard_peer.get('id')  if inboard_peer  else "None"
        outboard_id = outboard_peer.get('id') if outboard_peer else "None"

        for i, device in enumerate(self._device_list):
            num = i + 1
            id = device.get('id')
            name = device.get('name')
            mac_address = device.get('mac')
            enabled = device.get('enabled')
            in_range = '•' if self._is_peer_in_range(mac_address) else ''
            if not enabled:
                self._log.info(Style.DIM 
                        + "[{}]  id: {:<4} name: {:<34} ".format(num, id, name) 
                        + 'mac: ' + Fore.GREEN + '{}'.format(mac_address)
                        + Fore.CYAN + Style.NORMAL + " {}".format(in_range))
            elif mac_address == self._local_mac_str.lower():
                self._log.info("[{}]  id: ".format(num) 
                        + Style.BRIGHT + "{:<4} ".format(id) 
                        + Style.NORMAL + "name: "
                        + Style.BRIGHT + "{:<34} ".format(name)
                        + Style.NORMAL + "mac: " 
                        + Fore.GREEN + Style.BRIGHT + "{} •".format(mac_address))
            else:
                _color = Fore.GREEN if in_range else Fore.RED
                if not in_range:
                    _missing += 1
                if inboard_id == id or outboard_id == id:
                    self._log.info("[{}]  id: ".format(num) 
                            + _color + "{:<4} ".format(id) 
                            + Fore.CYAN + "name: "
                            + _color + "{:<34} ".format(name)
                            + Fore.CYAN + "mac: " 
                            + _color + "{}".format(mac_address)
                            + Fore.CYAN + " {}".format(in_range))
                else:
                    self._log.info("[{}]  id: ".format(num) 
                            + _color + "{:<4} ".format(id) 
                            + Fore.CYAN + "name: "
                            + _color + "{:<34} ".format(name)
                            + Fore.CYAN + "mac: " 
                            + _color + "{}".format(mac_address)
                            + Fore.CYAN + " {}".format(in_range))
        return _missing

    def _get_active_peers(self, current_index):
        '''
        Returns a tuple containing the nearest enabled inboard and outboard devices 
        (or None if the end of the chain is reached).
        '''
        inboard_peer = None
        outboard_peer = None
        # traverse backward to find the first enabled inboard device
        for i in range(current_index - 1, -1, -1):
            if self._device_list[i].get('enabled'):
                inboard_peer = self._device_list[i]
                break
        # traverse forward to find the first enabled outboard device
        for i in range(current_index + 1, len(self._device_list)):
            if self._device_list[i].get('enabled'):
                outboard_peer = self._device_list[i]
                break
        return inboard_peer, outboard_peer

    def _is_peer_in_range(self, mac_str):
        '''
        Sends a synchronous ping to a MAC address string to verify if it
        is within radio range. Returns True if acknowledged, False otherwise.
        '''
        if not self._encryption_enabled:
            try:
                mac_bytes = ubinascii.unhexlify(mac_str.replace(":", ""))
                try:
                    exists = any(peer[0] == mac_bytes for peer in self._espnow.get_peers())
                    if not exists:
                        self._espnow.add_peer(mac_bytes)
                    try:
                        # True parameter forces a synchronous send expecting an ACK
                        connected = bool(self._espnow.send(mac_bytes, b"\x00", True))
#                       self._log.debug('mac: {}; connected: {}'.format(mac_str, connected))
                        return connected
                    finally:
                        if not exists:
                            self._espnow.del_peer(mac_bytes)
                except OSError as e:
                    # ENODEV (error 19) indicates the peer did not ACK (out of range)
                    if len(e.args) > 0 and e.args[0] != 19:
                        self._log.error("ESP-NOW hardware error testing '{}': {}".format(mac_str, e))
                except Exception as e:
                    self._log.error("Unexpected error checking range for '{}': {}".format(mac_str, e))
            except ValueError as e:
                self._log.error("Invalid MAC address format '{}': {}".format(mac_str, e))
            except Exception as e:
                self._log.error("Unexpected error parsing MAC '{}': {}".format(mac_str, e))
        return False

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
        '''
        Asynchronously set the color of the pixel for a specified
        period of time, then return to black.
        '''
        self._show_color(color)
        await asyncio.sleep_ms(duration_ms)
        self._show_color(COLOR_BLACK)

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
