import re

def clean_price_string(price_str: str) -> str:
    """
    Cleans a string by removing all characters that interfere with parsing it as a float.

    Parameters:
        price_str (str): The input string containing a price.

    Returns:
        float: The cleaned price value.
    """
    # Use regex to keep only digits, decimal points, and negative sign
    cleaned_str = re.sub(r"[^\d.-]", "", price_str)

    # Handle edge cases and convert to float
    try:
        return str(float(cleaned_str))
    except ValueError:
        raise ValueError(f"Unable to parse '{price_str}' as a float.")