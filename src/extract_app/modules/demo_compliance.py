# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/demo_compliance.py
# Version: 1.0.0
# Author: Antigravity
# Description: A demonstration module to verify strict adherence to coding standards.
# --------------------------------------------------------------------------------

import sys
from typing import List, Optional

def calculate_factorial(n: int) -> int:
    """
    Calculates the factorial of a non-negative integer.

    Args:
        n (int): The non-negative integer to calculate the factorial of.

    Returns:
        int: The factorial of n.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("Input must be a non-negative integer.")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def greet_users(names: List[str], greeting: Optional[str] = "Hello") -> None:
    """
    Prints a greeting to a list of users.

    Args:
        names (List[str]): A list of user names.
        greeting (Optional[str]): The greeting to use. Defaults to "Hello".
    
    Returns:
        None
    """
    for name in names:
        print(f"{greeting}, {name}!")

if __name__ == "__main__":
    print("Running compliance demo...")
    try:
        fact_5 = calculate_factorial(5)
        print(f"Factorial of 5 is: {fact_5}")
        
        greet_users(["User", "Reviewer"], greeting="Greetings")
        print("Compliance check passed.")
    except Exception as e:
        print(f"Compliance check failed: {e}")
        sys.exit(1)
