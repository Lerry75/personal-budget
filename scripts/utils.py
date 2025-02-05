import os
import pandas as pd
import logging

def parse_and_filter_amount(amt_str: str) -> float:
    # Parse the original amount from CSV (which may have negative sign and comma decimals).
    # If the numeric value is > 0, return None to indicate to filter out that row.
    if not amt_str:
        return None
    try:
        # Replace comma with dot to parse as float
        numeric_val = float(amt_str.replace(',', '.'))
        if numeric_val > 0:
            # Income or positive row -> filter it out
            return None
        else:
            # It's negative or zero, we keep it but store as positive
            return abs(numeric_val)
    except ValueError:
        logging.warning(f"Could not parse amount: {amt_str}")
        return None
    
def get_person(input_file: str) -> str:
    filename = os.path.basename(input_file)
    parts = filename.split("-")
    if len(parts) > 1:
        if parts[1].strip().endswith(".csv"):
            person_value = "NoPerson"
        else:
            person_value = parts[1].strip()
    else:
        person_value = "NoPerson"

    return person_value

def format_amount(value: float) -> str:
    # Turn float -> "123.45" -> "123,45"
    if pd.isnull(value):
        return ''
    return str(value).replace('.', ',')