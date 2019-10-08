# -*- coding: utf-8 -*-
"""Configuration for pytest
"""

import pytest

@pytest.fixture
def input_value():
    """Example function with mock data."""
    return 123
