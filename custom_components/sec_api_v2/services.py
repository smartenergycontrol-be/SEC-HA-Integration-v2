"""Helper functions."""

import re


def format_id(input_str):
    """Format ids to hass standards."""
    input_str = input_str.replace("@", "a").replace("+", "_plus")
    formatted_str = re.sub(r"\W+", "_", input_str)
    formatted_str = re.sub(r"_+", "_", formatted_str)
    return formatted_str.strip("_").lower()
