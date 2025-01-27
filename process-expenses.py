import os
import sys
import csv
import logging
import glob
import shutil
from datetime import datetime

import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_config(config_file: str) -> dict:
    if not os.path.exists(config_file):
        logging.error(f"Config file not found: {config_file}")
        sys.exit(1)

    with open(config_file, 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Failed parsing config file: {e}")
            sys.exit(1)

    if 'paths' not in config:
        logging.error(f"Missing 'paths' key in {config_file}.")
        sys.exit(1)

    setup_paths(config['paths'])

    return config['paths']

def setup_paths(paths: dict):
    # Create input folder if not exist
    input_folder = paths.get('input_folder')
    if input_folder and not os.path.exists(input_folder):
        try:
            os.makedirs(input_folder)
            logging.info(f"Created folder: {input_folder}")
        except Exception as e:
            logging.error(f"Failed to create folder {input_folder}: {e}")
            sys.exit(1)

    # Create processed folder if not exist
    processed_folder = paths.get('processed_folder')
    if processed_folder and not os.path.exists(processed_folder):
        try:
            os.makedirs(processed_folder)
            logging.info(f"Created folder: {processed_folder}")
        except Exception as e:
            logging.error(f"Failed to create folder {processed_folder}: {e}")
            sys.exit(1)

    # Create output folder if not exist
    output_folder = paths.get('output_folder')
    if output_folder and not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
            logging.info(f"Created folder: {output_folder}")
        except Exception as e:
            logging.error(f"Failed to create folder {output_folder}: {e}")
            sys.exit(1)

    # Check category file
    category_file = paths.get('category_file')
    if not category_file or not os.path.exists(category_file):
        logging.error(f"category_file does not exist or not specified: {category_file}")
        sys.exit(1)

def load_category_rules(yaml_path: str) -> list:
    # Loads category classification rules from a YAML file.
    if not os.path.exists(yaml_path):
        logging.error(f"Category rules file not found: {yaml_path}")
        sys.exit(1)
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    rules = config.get('rules', [])
    if not rules:
        logging.error("No 'rules' key found in the YAML or it's empty.")
        sys.exit(1)
    return rules

def categorize_expense(note: str, rules: list) -> str:
    # Catecorize a single note against the loaded rules.
    note_upper = note.strip().upper() if note else ""

    for rule in rules:
        rule_type = rule.get('type', '').lower()
        pattern = rule.get('pattern', '')
        category = rule.get('category', 'Uncategorized')
        if rule_type == 'startswith':
            if note_upper.startswith(pattern.upper()):
                return category
        elif rule_type == 'contains':
            if pattern.upper() in note_upper:
                return category
        elif rule_type == 'endswith':
            if note_upper.endswith(pattern.upper()):
                return category
        elif rule_type == 'regex':
            import re
            if re.search(pattern, note, re.IGNORECASE):
                return category
        elif rule_type == 'default':
            return category

    return "Uncategorized"

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

def process_file(
    input_file: str,
    category_rules: list,
    output_folder: str,
    file_index: int
):
    # Read input CSV
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        return

    try:
        df = pd.read_csv(input_file, sep=';', dtype=str, keep_default_na=False)
    except Exception as e:
        logging.error(f"Failed reading CSV {input_file}: {e}")
        return

    if 'Booking date' not in df.columns or 'Amount' not in df.columns or 'Title' not in df.columns:
        logging.error("CSV must have at least 'Booking date', 'Amount', 'Title' columns.")
        return

    # Parse date (assume data is in yyyy/MM/dd format)
    df['Date_parsed'] = pd.to_datetime(df['Booking date'], format='%Y/%m/%d', errors='coerce')
    df['Year'] = df['Date_parsed'].dt.year.fillna(0).astype(int).astype(str)
    df['Month'] = df['Date_parsed'].dt.month_name().str[:3].fillna('')

    # Filter out rows with Amount > 0
    df['Amount_float'] = df['Amount'].apply(parse_and_filter_amount)
    # Drop rows where Amount_float is None
    before_count = len(df)
    df = df.dropna(subset=['Amount_float'])
    after_count = len(df)
    logging.info(f"Filtered out {before_count - after_count} rows with amount > 0.")

    # Convert the numeric float to a string with comma decimals for final display
    df['Amount_clean'] = df['Amount_float'].apply(format_amount)

    # Categorize the note
    df['Category'] = df['Title'].apply(lambda nt: categorize_expense(nt, category_rules))

    # Set Person, Type
    person_value = get_person(input_file)
    if 'Person' not in df.columns:
        df['Person'] = person_value

    if 'Type' not in df.columns:
        df['Type'] = "Actual"

    # Select final columns
    final_cols = ["Year", "Month", "Amount_clean", "Category", "Person", "Type", "Title"]
    # Keep only columns that exist
    final_cols = [c for c in final_cols if c in df.columns]
    final_df = df[final_cols].copy()
    # Rename columns
    final_df.rename(columns={"Amount_clean": "Amount DKK"}, inplace=True)
    final_df.rename(columns={"Title": "Notes"}, inplace=True)

    # Writes output CSV: 'Expenses-{Person}-{yyyy}{MM}{dd}-{hh}{mm}-{index}.csv'
    output_base = "Expenses"
    output_endname = datetime.now().strftime("%Y%m%d-%H%M")
    output_name = f"{output_base}-{person_value}-{output_endname}-{file_index}.csv"
    output_path = os.path.join(output_folder, output_name)

    try:
        final_df.to_csv(output_path, sep=';', index=False)
        logging.info(f"Processed {input_file} -> {output_path} (kept {len(final_df)} rows)")
    except Exception as e:
        logging.error(f"Failed writing output CSV {output_path}: {e}")

def move_file(
    input_file: str,
    output_folder: str
):
    try:
        file_name = os.path.basename(input_file)
        destination = os.path.join(output_folder, file_name)

        shutil.move(input_file, destination)
        logging.info(f"File moved to {destination}.")
    except FileNotFoundError:
        logging.error("Error: The file '{input_file}' does not exist.")
    except Exception as e:
        logging.error(f"Error: {str(e)}")

def main():
    config_file = "./config.yaml"
    paths = load_config(config_file)

    # Load category rules
    rules = load_category_rules(paths['category_file'])
    logging.info(f"Loaded {len(rules)} category rules from {paths['category_file']}")

    for index, csv_file in enumerate(glob.glob(os.path.join(paths['input_folder'], "*.csv"))):
        process_file(csv_file, rules, paths['output_folder'], index)
        move_file(csv_file, paths['processed_folder'])

if __name__ == "__main__":
    main()
