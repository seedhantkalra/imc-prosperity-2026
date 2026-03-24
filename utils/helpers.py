"""Shared helpers for strategy development."""

def clamp(value: int | float, low: int | float, high: int | float):
    return max(low, min(high, value))
