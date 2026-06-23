#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2026 by Ichiro Furusato. All rights reserved. This file is part
# of the Robot Operating System project, released under the MIT License.
#
# author:   Ichiro Furusato
# created:  2026-06-23
# modified: 2026-06-23

import random

class FoodNameGenerator:

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
    def generate(cls):
        return "{} {}".format(
            random.choice(cls._ADJECTIVES),
            random.choice(cls._NOUNS)
        )

#EOF
