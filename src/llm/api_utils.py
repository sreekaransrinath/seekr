"""Utilities for API key validation and management."""
from typing import Optional


def is_valid_api_key(key: Optional[str]) -> bool:
    """
    Check if API key is valid (not None, empty, or a placeholder value).

    Args:
        key: API key to validate

    Returns:
        True if key is valid, False if None/empty/placeholder

    Example:
        >>> is_valid_api_key("sk-1234567890abcdef")
        True
        >>> is_valid_api_key("your_api_key_here")
        False
        >>> is_valid_api_key(None)
        False
        >>> is_valid_api_key("")
        False
    """
    if not key:
        return False

    # Common placeholder patterns
    placeholders = [
        "your_",
        "placeholder",
        "xxx",
        "key_here",
        "api_key_here",
        "enter_your",
        "replace_this",
        "add_your",
    ]

    key_lower = key.lower()
    return not any(placeholder in key_lower for placeholder in placeholders)
