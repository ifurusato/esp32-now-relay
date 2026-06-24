#!/micropython
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License. Please
# see the LICENSE file included as part of this package.
#
# author:   Ichiro Furusato
# created:  2026-06-23
# modified: 2026-06-23

from component import Component
from logger import Logger, Level
from event import *

class MessageCodec(Component):
    NAME = 'msg-codec'
    DELIMITER = '|'
    '''
    Handles the serialization and deserialization of Message objects for network transport.
    '''
    def __init__(self, message_factory=None, level=Level.INFO):
        Component.__init__(self, MessageCodec.NAME, suppressed=False, enabled=True, level=level)
        self._message_factory = message_factory
        self._delimiter = MessageCodec.DELIMITER # could come from config
        self._log.info('ready.')

    def serialize(self, direction, message):
        '''
        Serializes a Message instance and its network direction into a pipe-delimited payload string.

        :param direction: the network travel direction (int)
        :param message: the Message instance to encode
        :return: a formatted string ready for transmission
        '''
        _val_str = message.value if message.value is not None else ""
        return "{}{}{}{}{}{}{}{}{}".format(
            direction,           self._delimiter,
            message.id,          self._delimiter,
            message.event.label, self._delimiter,
            _val_str,            self._delimiter,
            message.timestamp
        )

    def deserialize(self, payload_str):
        '''
        Parses a received pipe-delimited payload string back into its constituent direction
        and a fully reconstructed Message instance.

        :param payload_str: the raw un-encoded string received from the network
        :return: a tuple of (direction, reconstructed_message) or (None, None) if malformed
        '''
        # split exactly 4 times to safely isolate the 5 expected fields
        parts = payload_str.split(self._delimiter, 4)
        if len(parts) < 5:
            self._log.error('payload string had {} parts rather than 5.'.format(len(parts)))
            return None, None
        try:
            direction   = int(parts[0])
            msg_id      = parts[1]
            event       = Event.by_label(parts[2])
            raw_value   = parts[3]
            timestamp   = float(parts[4])
            value_payload = raw_value if raw_value != "" else None
            # reconstruct Message instance via factory context
            reconstructed_msg = self._message_factory.create_message(
                event=event,
                value=value_payload
            )
            # explicitly re-apply the tracking state metadata from transport layout
            reconstructed_msg.id = msg_id
            reconstructed_msg.timestamp = timestamp
            return direction, reconstructed_msg
        except (ValueError, TypeError) as e:
            # guard against corrupted integers, floats, or conversion mismatches
            self._log.error('{} raised deserialising message: {}'.format(type(e), e))
            return None, None

#EOF
