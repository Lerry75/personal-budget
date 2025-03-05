import re
import csv
import logging
import glob
import os
import sys
import datetime
from config_loader import load_config
from entries_processor import move_file_to_archive

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def clean_amount(amount_str):
    """
    Remove thousand separators (periods) and ensure the amount is negative.
    The input is assumed to have a comma as the decimal separator.
    E.g., "1.124,93" -> "-112493", then reinsert comma to yield "-1124,93"
    """
    try:
        # Remove any thousand separators (periods)
        cleaned = amount_str.replace('.', '')
        cleaned = cleaned.strip()
        # Ensure the amount starts with a minus sign
        if not cleaned.startswith('-'):
            cleaned = '-' + cleaned
        return cleaned
    except Exception as e:
        logging.exception(f"Error cleaning amount '{amount_str}'")
        raise

def parse_input_file(input_filename):
    """
    Parses the input file and returns a list of transactions.
    Each transaction is a dict with keys: Booking date, Title, Amount.
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
            logging.info(f"Opened input file '{input_filename}' for reading.")
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

def assign_years(transactions):
    """
    Updates each transaction's 'Booking date' to include the year.
    - If only one month is present, all transactions get the current year.
    - If the two months are {12, 01}, then transactions in January get the current year
      and those in December get the previous year.
    - Otherwise, assume all transactions belong to the current year.
    """
    current_year = datetime.date.today().year
    months = set()

    for t in transactions:
        try:
            parts = t["Booking date"].split('/')
            if len(parts) < 2:
                continue
            months.add(int(parts[1]))
        except Exception:
            logging.error(f"Failed to parse month from booking date: {t['Booking date']}")

    logging.info(f"Distinct months found in transactions: {months}")

    # Assign years based on the months found.
    if len(months) == 1:
        for t in transactions:
            t["Booking date"] = f"{t['Booking date']}/{current_year}"
    elif months == {1, 12}:
        for t in transactions:
            try:
                month = int(t["Booking date"].split('/')[1])
                if month == 1:
                    t["Booking date"] = f"{t['Booking date']}/{current_year}"
                elif month == 12:
                    t["Booking date"] = f"{t['Booking date']}/{current_year - 1}"
            except Exception:
                logging.error(f"Failed to assign year for booking date: {t['Booking date']}")
    else:
        # If there are two months but they are not {1, 12}, assume all transactions are in the current year.
        for t in transactions:
            t["Booking date"] = f"{t['Booking date']}/{current_year}"

    logging.info("Year assignment to booking dates complete.")
    return transactions

def write_output_file(output_filename, transactions):
    """
    Writes the transactions to a CSV file with the specified output filename.
    The CSV uses a semicolon as separator and no text qualifiers.
    """
    fieldnames = ["Booking date", "Title", "Amount"]
    try:
        with open(output_filename, "w", newline='', encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
            writer.writeheader()
            writer.writerows(transactions)
        logging.info(f"Output file '{output_filename}' has been created with {len(transactions)} transactions.")
    except Exception:
        logging.exception("An error occurred while writing the output file.")
        sys.exit(1)

def main():
    paths = load_config('config.yaml')
    #input_filename = "input-entries.txt"
    output_filename = "output-entries.csv"

    logging.info("Starting conversion process.")
    processed_file_no = 0
    txt_files = glob.glob(os.path.join(paths['input_folder'], "*.txt"))
    for index, txt_file in enumerate(txt_files):
        try:
            transactions = parse_input_file(txt_file)
            transactions = assign_years(transactions)
            # Write the outputfile following the naming convention
            write_output_file(output_filename, transactions)    # to be modified
            move_file_to_archive(txt_file, paths['processed_folder'])
            processed_file_no += 1
        except Exception as e:
            logging.error(f"Failed to convert {txt_file}: {type(e).__name__} - {e}")
            continue

    logging.info(f"{processed_file_no} file(s) converted.")

if __name__ == "__main__":
    main()
