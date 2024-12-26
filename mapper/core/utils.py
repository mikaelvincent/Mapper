"""
Utility functions for CLI parameter parsing.
"""

import click

def int_or_none(ctx, param, value):
    """
    Custom callback for Click to interpret a string of "None" as None,
    or otherwise parse the value as an integer.
    """
    if value is None:
        return None
    if value.lower() == "none":
        return None
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter(f"Invalid integer value: {value}")

def bool_or_none(ctx, param, value):
    """
    Custom callback for Click to interpret possible strings as booleans
    if they are not None or 'None'.
    """
    if value is None:
        return None
    val_lower = value.lower()
    if val_lower == "none":
        return None
    return val_lower in ("true", "1", "yes")
