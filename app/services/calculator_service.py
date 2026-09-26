"""Calculator service demonstrating the business logic layer."""

from typing import Union


class CalculatorService:
    """Service class encapsulating mathematical and calculation operations."""

    @staticmethod
    def add(num1: Union[int, float], num2: Union[int, float]) -> Union[int, float]:
        """Calculates the sum of two numbers, preserving integer type if both are ints."""
        result = num1 + num2
        # Cleanly return int if both inputs and result are whole numbers
        if isinstance(num1, int) and isinstance(num2, int):
            return int(result)
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return round(result, 4)
