"""Utility functions for CryptoLab BB84.

This module contains common helper functions used across the codebase,
promoting code reuse and reducing duplication.
"""

from __future__ import annotations

from typing import Any, Sequence
import numpy as np


def bits_to_string(bits: Sequence[int]) -> str:
    """Convert a sequence of bits to a string representation.
    
    Args:
        bits: Sequence of 0s and 1s
        
    Returns:
        String representation of bits
        
    Example:
        >>> bits_to_string([0, 1, 1, 0])
        '0110'
    """
    return "".join(map(str, bits))


def string_to_bits(bit_string: str) -> list[int]:
    """Convert a string of bits to a list of integers.
    
    Args:
        bit_string: String containing only '0' and '1' characters
        
    Returns:
        List of integers (0s and 1s)
        
    Raises:
        ValueError: If string contains non-binary characters
        
    Example:
        >>> string_to_bits('0110')
        [0, 1, 1, 0]
    """
    if not all(c in '01' for c in bit_string):
        raise ValueError("Bit string must contain only '0' and '1' characters")
    return [int(c) for c in bit_string]


def hamming_distance(seq1: Sequence[int], seq2: Sequence[int]) -> int:
    """Calculate Hamming distance between two sequences.
    
    Args:
        seq1: First sequence
        seq2: Second sequence
        
    Returns:
        Number of positions where sequences differ
        
    Raises:
        ValueError: If sequences have different lengths
        
    Example:
        >>> hamming_distance([0, 1, 1, 0], [0, 0, 1, 1])
        2
    """
    if len(seq1) != len(seq2):
        raise ValueError("Sequences must have the same length")
    return sum(a != b for a, b in zip(seq1, seq2))


def calculate_error_rate(seq1: Sequence[int], seq2: Sequence[int]) -> float:
    """Calculate error rate between two sequences.
    
    Args:
        seq1: First sequence
        seq2: Second sequence
        
    Returns:
        Error rate as a float between 0 and 1
        
    Raises:
        ValueError: If sequences have different lengths or are empty
        
    Example:
        >>> calculate_error_rate([0, 1, 1, 0], [0, 0, 1, 1])
        0.5
    """
    if len(seq1) == 0:
        raise ValueError("Sequences cannot be empty")
    if len(seq1) != len(seq2):
        raise ValueError("Sequences must have the same length")
    return hamming_distance(seq1, seq2) / len(seq1)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Value to return if denominator is zero
        
    Returns:
        Result of division or default value
        
    Example:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0, default=0.0)
        0.0
    """
    return numerator / denominator if denominator != 0 else default


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Clamped value
        
    Example:
        >>> clamp(5, 0, 10)
        5
        >>> clamp(-5, 0, 10)
        0
        >>> clamp(15, 0, 10)
        10
    """
    return max(min_value, min(value, max_value))


def percentage(value: float, decimals: int = 2) -> float:
    """Convert a fraction to a percentage.
    
    Args:
        value: Fraction value (0 to 1)
        decimals: Number of decimal places
        
    Returns:
        Percentage value (0 to 100)
        
    Example:
        >>> percentage(0.25)
        25.0
        >>> percentage(0.12345, decimals=3)
        12.345
    """
    return round(value * 100, decimals)


def format_key_preview(key: str, max_length: int = 64) -> str:
    """Format a key string for display, truncating if necessary.
    
    Args:
        key: Key string to format
        max_length: Maximum length before truncation
        
    Returns:
        Formatted key string
        
    Example:
        >>> format_key_preview('0' * 100, max_length=10)
        '0000000000...'
    """
    if len(key) <= max_length:
        return key
    return key[:max_length] + "..."


def validate_probability(value: float, name: str = "probability") -> None:
    """Validate that a value is a valid probability (0 to 1).
    
    Args:
        value: Value to validate
        name: Name of the parameter for error messages
        
    Raises:
        ValueError: If value is not between 0 and 1
        
    Example:
        >>> validate_probability(0.5)
        >>> validate_probability(1.5)
        Traceback (most recent call last):
        ...
        ValueError: probability must be between 0 and 1, got 1.5
    """
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def validate_positive_int(value: int, name: str = "value", min_value: int = 1) -> None:
    """Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        name: Name of the parameter for error messages
        min_value: Minimum allowed value
        
    Raises:
        ValueError: If value is not a positive integer
        TypeError: If value is not an integer
        
    Example:
        >>> validate_positive_int(10)
        >>> validate_positive_int(-5)
        Traceback (most recent call last):
        ...
        ValueError: value must be at least 1, got -5
    """
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    if value < min_value:
        raise ValueError(f"{name} must be at least {min_value}, got {value}")


def estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    """Estimate token count from text length.
    
    This is a rough approximation used for cost estimation.
    
    Args:
        text: Text to estimate tokens for
        chars_per_token: Average characters per token
        
    Returns:
        Estimated token count
        
    Example:
        >>> estimate_tokens("Hello world")
        3
    """
    return max(1, int(len(text) / chars_per_token))


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
        
    Example:
        >>> format_duration(0.5)
        '500.0ms'
        >>> format_duration(1.5)
        '1.50s'
        >>> format_duration(65)
        '1m 5s'
    """
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"


def truncate_middle(text: str, max_length: int = 50, separator: str = "...") -> str:
    """Truncate text in the middle, keeping start and end.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of result
        separator: Separator to use in the middle
        
    Returns:
        Truncated text
        
    Example:
        >>> truncate_middle("0123456789", max_length=8)
        '01...89'
    """
    if len(text) <= max_length:
        return text
    
    sep_len = len(separator)
    if max_length <= sep_len:
        return separator[:max_length]
    
    side_length = (max_length - sep_len) // 2
    return text[:side_length] + separator + text[-side_length:]


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_config_dict(config: dict[str, Any], required_keys: set[str]) -> None:
    """Validate that a configuration dictionary has all required keys.
    
    Args:
        config: Configuration dictionary to validate
        required_keys: Set of required key names
        
    Raises:
        ValidationError: If any required keys are missing
        
    Example:
        >>> validate_config_dict({'a': 1, 'b': 2}, {'a', 'b'})
        >>> validate_config_dict({'a': 1}, {'a', 'b'})
        Traceback (most recent call last):
        ...
        ValidationError: Missing required configuration keys: b
    """
    missing = required_keys - set(config.keys())
    if missing:
        raise ValidationError(f"Missing required configuration keys: {', '.join(sorted(missing))}")


def numpy_to_python(obj: Any) -> Any:
    """Convert NumPy types to native Python types for JSON serialization.
    
    Args:
        obj: Object to convert
        
    Returns:
        Python native type
        
    Example:
        >>> import numpy as np
        >>> numpy_to_python(np.int64(42))
        42
        >>> numpy_to_python(np.array([1, 2, 3]))
        [1, 2, 3]
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj

# Made with Bob
