# -*- coding: utf-8 -*-
"""Sample tests
"""

from dcmweb import place_holder
def test_place_holder(input_value):
    """Example test."""
    assert place_holder.string(input_value) == "placeholder123", "bad test"
