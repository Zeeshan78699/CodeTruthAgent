"""Small passing test suite."""

from safe_module import format_currency, greet

def test_format_currency():
    assert format_currency(1000) == "$1,000.00"

def test_greet():
    assert greet("world") == "Hello, world"
