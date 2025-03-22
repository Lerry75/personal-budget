import os
import re
import sys
import pandas as pd
import logging
from utils.utils import parse_amount, get_person, format_amount, clean_amount

def get_df_from_csv_nordea(input_file: str) -> { pd.DataFrame, pd.DataFrame }:
    """ 
    Read a CSV file produced from Nordea Netbank platform and return a dictionary with income and expenses dataframes. 
    """
    # Read input CSV
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logging.info(f"Processing '{os.path.relpath(input_file)}'...")
    df = pd.read_csv(input_file, sep=';', dtype=str, keep_default_na=False)

    if 'Booking date' not in df.columns or 'Amount' not in df.columns or 'Title' not in df.columns:
        raise ValueError("CSV must have at least 'Booking date', 'Amount', 'Title' columns.")

    # Parse date (assume data is in yyyy/MM/dd format)
    try:
        df['Date_parsed'] = pd.to_datetime(df['Booking date'], format='%Y/%m/%d', errors='raise')
    except ValueError:
        try:
            df['Date_parsed'] = pd.to_datetime(df['Booking date'], format='%d/%m/%Y', errors='raise')
        except ValueError:
            df['Date_parsed'] = pd.to_datetime(df['Booking date'], format='mixed', errors='coerce')

    df['Year'] = df['Date_parsed'].dt.year.fillna(0).astype(int).astype(str)
    df['Month'] = df['Date_parsed'].dt.month_name().str[:3].fillna('')
    df['Amount_float'] = df['Amount'].apply(parse_amount)

    # Convert the numeric float to a string with comma decimals for final display
    df['Amount_clean'] = df['Amount_float'].apply(format_amount)

    # Set Person, Type
    person_value = get_person(input_file)
    if 'Person' not in df.columns:
        df['Person'] = person_value

    if 'Type' not in df.columns:
        df['Type'] = "Actual"

    # Rename columns
    df['Amount'] = df['Amount_float'].abs()
    df.rename(columns={"Amount_clean": "Amount DKK"}, inplace=True)
    df.rename(columns={"Title": "Notes"}, inplace=True)

    # Create dataframes for income and expenses
    income = df[df["Amount_float"] > 0]
    expenses = df[df["Amount_float"] < 0].copy()  # Create an explicit copy
    expenses.loc[:, "Amount_float"] = expenses["Amount_float"].abs()  # Use .loc for assignment

    return { "income": income, "expenses": expenses }

def parse_cc_statement_file(input_filename: str) -> list:
    """ 
    Parses the input TXT file from the credit card statement and returns a list of transactions.
    """
    transactions = []
    pending_transaction = None

    # Regular expression for a header line.
    # It captures:
    #   date: two digits/two digits (e.g., 15/12)
    #   description: merchant information (which starts with "VAREKØB - " and then the merchant)
    #   an optional amount at the end (if the transaction is local in DKK)
    header_pattern = re.compile(
        r'^(?P<date>\d{2}/\d{2}):\s+(?P<description>.+?)(?:\s+(?P<amount>[\d\.]+,\d{2}))?\s*$'
    )

    # Regular expression for a detail line for a foreign transaction.
    # It captures:
    #   currency (3 uppercase letters)
    #   foreign amount (ignored)
    #   dk_amount: the final DKK equivalent amount
    detail_pattern = re.compile(
        r'^\.\s+(?P<currency>[A-Z]{3})\s+(?P<foreign_amount>[\d\.]+,\d{2})\s+(?P<dk_amount>[\d\.]+,\d{2})'
    )

    try:
        with open(input_filename, "r", encoding="utf-8") as infile:
            logging.info(f"Opened input file '{os.path.relpath(input_filename)}' for reading.")
            for lineno, line in enumerate(infile, start=1):
                line = line.rstrip("\n")
                if not line.strip():
                    continue  # Skip empty lines

                # Check if the line is a header line (starts with a date like "15/12:")
                header_match = header_pattern.match(line)
                if header_match:
                    # If there is a pending foreign transaction without detail, log a warning.
                    if pending_transaction is not None:
                        logging.warning(f"Line {lineno}: Previous foreign transaction missing detail line. Saving it as-is.")
                        transactions.append(pending_transaction)
                        pending_transaction = None

                    date = header_match.group("date")
                    description = header_match.group("description").strip()
                    # Remove "VAREKØB - " prefix if present
                    prefix = "VAREKØB - "
                    if description.startswith(prefix):
                        description = description[len(prefix):].strip()

                    amount = header_match.group("amount")
                    if amount:
                        try:
                            clean_amt = clean_amount(amount)
                        except Exception:
                            logging.error(f"Line {lineno}: Failed to clean amount '{amount}'. Skipping this line.")
                            continue

                        transactions.append({
                            "Booking date": date,
                            "Title": description,
                            "Amount": clean_amt
                        })
                    else:
                        # This is a foreign transaction; save header info and expect a detail line next.
                        pending_transaction = {
                            "Booking date": date,
                            "Title": description,
                            "Amount": ""  # to be filled from the detail line
                        }
                    continue

                # Check if the line is a detail line (begins with a dot).
                if line.startswith("."):
                    detail_match = detail_pattern.match(line)
                    if detail_match and pending_transaction is not None:
                        dk_amount = detail_match.group("dk_amount")
                        try:
                            clean_amt = clean_amount(dk_amount)
                        except Exception:
                            logging.error(f"Line {lineno}: Failed to clean detail amount '{dk_amount}'. Skipping this transaction.")
                            pending_transaction = None
                            continue
                        pending_transaction["Amount"] = clean_amt
                        transactions.append(pending_transaction)
                        pending_transaction = None
                    else:
                        logging.warning(f"Line {lineno}: Detail line encountered without a pending header transaction or pattern mismatch.")
                    continue

                # If line doesn't match header or detail, log a warning.
                logging.warning(f"Line {lineno}: Unrecognized format: {line}")
    except FileNotFoundError:
        logging.exception(f"Input file '{input_filename}' not found.")
        sys.exit(1)
    except Exception:
        logging.exception("An error occurred while parsing the input file.")
        sys.exit(1)

    logging.info(f"Parsed {len(transactions)} transactions from input file.")
    return transactions