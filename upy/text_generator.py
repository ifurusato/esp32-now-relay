#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License.
#
# author:   Ichiro Furusato
# created:  2026-06-23
# modified: 2026-06-28
#
# ESP-NOW RELAY

import random

class TextGenerator:

    _LOREM_IPSUM = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum bibendum justo sit amet augue fermentum placerat. Cras vel posuere metus. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Praesent ac dolor malesuada, rhoncus orci sit amet, tristique metus. Integer sit amet convallis lorem, consectetur pretium elit. Quisque ultrices viverra eros dapibus laoreet. Mauris et sapien ac neque pharetra convallis id sed lorem.
In nec pulvinar erat. Nulla et augue elementum, scelerisque ligula a, posuere quam. Cras lobortis dignissim lectus id semper. Sed euismod lacus et nibh scelerisque, convallis elementum elit egestas. Sed non hendrerit lacus, ac ullamcorper lorem. Nulla purus leo, tempor sed dui in, viverra sollicitudin tellus. Sed id odio eu odio bibendum condimentum. Ut convallis in leo eget mollis. Duis ex eros, dapibus sit amet tortor eu, dapibus volutpat nulla. Praesent ac risus sed sem sodales mollis sed in nunc. Donec varius mi nunc, nec semper magna mattis sit amet. Duis placerat, lectus in ornare ullamcorper, tortor nunc bibendum neque, nec finibus tortor est sed turpis. Duis vel hendrerit massa.
Morbi a urna vitae arcu facilisis pellentesque a id purus. In tincidunt massa ac velit auctor laoreet. Donec bibendum nibh ut neque rutrum viverra quis sit amet tortor. Maecenas ut nisl sit amet lectus venenatis vestibulum. Suspendisse magna ipsum, condimentum a turpis a, euismod congue leo. Class aptent taciti sociosqu ad litora efficitur. 
"""

    _ADJECTIVES = (
        "buttery",
        "fresh",
        "hearty",
        "crispy",
        "sweet",
        "savory",
        "creamy",
        "tangy",
        "golden",
        "spicy",
        "juicy",
        "smoky",
        "zesty",
        "fluffy",
        "rich",
        "toasted",
    )

    _NOUNS = (
        "pancakes",
        "milk",
        "tomatoes",
        "apples",
        "bread",
        "cheese",
        "cookies",
        "potatoes",
        "carrots",
        "muffins",
        "waffles",
        "berries",
        "soup",
        "noodles",
        "peppers",
        "beans",
    )

    @classmethod
    def generate_food_name(cls):
        return "{} {}".format(
            random.choice(cls._ADJECTIVES),
            random.choice(cls._NOUNS)
        )

    @classmethod
    def generate_lorem_ipsum(cls, length):
        return cls._LOREM_IPSUM[:length]

#EOF
