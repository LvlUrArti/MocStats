"""Calculate the specified percentile of an array using linear interpolation."""

import numpy as np


def calculate_percentile(custom_array: list[int], percentile: float) -> float:
    """Calculate the specified percentile of an array using linear interpolation."""
    """Parameters:
        custom_array (list or numpy array): The input array.
        percentile (float): The desired percentile (e.g., 25 for 25th percentile).

    Returns:
        float: The interpolated value at the specified percentile.
    """
    # Get unique values and their frequencies
    unique_values, counts = np.unique(custom_array, return_counts=True)

    # Calculate cumulative frequencies
    cumulative_frequencies = np.cumsum(counts)

    # Total number of data points
    total = len(custom_array)

    # Calculate the position of the percentile in the cumulative distribution
    position = percentile * total / 100

    # Find the index where the cumulative frequency exceeds the position
    idx = np.searchsorted(cumulative_frequencies, position, side="right")

    # Handle edge cases
    if idx == 0:
        return unique_values[0]
    if idx >= len(unique_values):
        return unique_values[-1]

    # Perform linear interpolation
    x1 = unique_values[idx - 1]
    x2 = unique_values[idx]
    p1 = cumulative_frequencies[idx - 1]
    p2 = cumulative_frequencies[idx]

    return x1 + (position - p1) / (p2 - p1) * (x2 - x1)


example = False
if example:
    # Example usage
    # Custom array taken from Firefly's E0S1 cycles for versioin 3.0
    custom_array = [5] * 4 + [6] * 12 + [7] * 43 + [8] * 105 + [9] * 172 + [10] * 269

    # Calculate specific percentiles
    q1 = calculate_percentile(custom_array, 25)
    median = calculate_percentile(custom_array, 50)
    q3 = calculate_percentile(custom_array, 75)

    print("25th Percentile (Q1):", q1)
    print("50th Percentile (Median):", median)
    print("75th Percentile (Q3):", q3)
