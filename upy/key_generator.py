#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Murray Altheim. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Murray Altheim
# created:  2026-06-23
# modified: 2026-06-23
#
# ESP-NOW RELAY

from uuid import UUID, uuid4
from config_loader import ConfigLoader
from logger import Logger, Level

class KeyGenerator:
    '''
    Handles the generation and writing of the secondary cryptographic keys configuration
    file based on a read-only source configuration.
    '''
    @staticmethod
    def generate_keys(config_path='config.yaml', output_path='keys.yaml'):
        log = Logger('key-gen', level=Level.INFO)
        try:
            log.info('loading configuration…')
            # load the original read-only configuration
            config = ConfigLoader.configure(config_path)
            device_list = config['relay']['devices']
            log.info('loaded configuration for {} devices.'.format(len(device_list)))

            generated_devices = {}

            # iterate and generate a unique 16-byte LMK for every device
            for device in device_list:
                mac_address = device.get('mac')
                if mac_address:
                    uuid_obj = uuid4()
                    generated_devices[mac_address] = uuid_obj.hex
                    log.info('generated key for device with MAC address: {}'.format(mac_address))

            # generate a unique 16-byte PMK for the global network configuration
            global_pmk = uuid4().hex
            log.info('generated global key.')

            # 3. Write out the stripped secondary keys configuration file safely
            log.info('writing output to: {}'.format(output_path))
            with open(output_path, 'w') as f:
                f.write('# Generated network encryption keys map\n')
                f.write('relay:\n')
                f.write('  pmk: "{}"\n'.format(global_pmk))
                f.write('  devices:\n')
                for mac, lmk in generated_devices.items():
                    f.write('    "{}": "{}"\n'.format(mac, lmk))

            log.info('complete.')
            return True
        except Exception as e:
            # re-raise or handle structurally depending on application logging requirements
            log.error('failed to generate keys configuration: {}'.format(e))
            raise RuntimeError('failed to generate keys configuration: {}'.format(e))

#EOF
