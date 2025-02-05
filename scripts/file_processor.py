import os
import shutil
import pandas as pd
import logging
from datetime import datetime
from utils import parse_and_filter_amount, get_person, format_amount
from dataset_enricher import enrich_dataframe, get_feature_list
from category_map import categorize_row

def process_input_file(input_file: str) -> pd.DataFrame:
    # Read input CSV
    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        return
    
    logging.info(f"Processing {input_file}...")
    try:
        df = pd.read_csv(input_file, sep=';', dtype=str, keep_default_na=False)
    except Exception as e:
        logging.error(f"Failed reading CSV {input_file}: {e}")
        return

    if 'Booking date' not in df.columns or 'Amount' not in df.columns or 'Title' not in df.columns:
        logging.error("CSV must have at least 'Booking date', 'Amount', 'Title' columns.")
        return

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

    # Filter out rows with Amount > 0
    df['Amount_float'] = df['Amount'].apply(parse_and_filter_amount)
    # Drop rows where Amount_float is None
    before_count = len(df)
    df = df.dropna(subset=['Amount_float'])
    after_count = len(df)
    logging.info(f"Filtered out {before_count - after_count} rows with amount > 0.")

    # Convert the numeric float to a string with comma decimals for final display
    df['Amount_clean'] = df['Amount_float'].apply(format_amount)

    # Set Person, Type
    person_value = get_person(input_file)
    if 'Person' not in df.columns:
        df['Person'] = person_value

    if 'Type' not in df.columns:
        df['Type'] = "Actual"

    # Rename columns
    df['Amount'] = df['Amount_float']
    df.rename(columns={"Amount_clean": "Amount DKK"}, inplace=True)
    df.rename(columns={"Title": "Notes"}, inplace=True)

    return df

def categorize_expenses_re(df: pd.DataFrame, category_rules: list):
    df['Category'] = df.apply(lambda row: categorize_row(row, category_rules), axis=1)

def categorize_expenses_ml(df: pd.DataFrame, model):
    enrich_dataframe(df)
    features = df[get_feature_list()]

    # Predict Categories
    try:
        df['Category'] = model.predict(features)
    except Exception as e:
        logging.error(f"Error during prediction: {e}")

def write_output_file(df: pd.DataFrame,
    input_file: str,
    output_folder: str,
    file_index: int):

    # Select final columns
    final_cols = ["Year", "Month", "Amount DKK", "Category", "Person", "Type", "Notes"]
    # Keep only columns that exist
    final_cols = [c for c in final_cols if c in df.columns]
    final_df = df[final_cols].copy()

    # Writes output CSV: 'Expenses-{Person}-{yyyy}{MM}{dd}-{hh}{mm}-{index}.csv'
    output_base = "Expenses"
    output_endname = datetime.now().strftime("%Y%m%d-%H%M")
    output_name = f"{output_base}-{get_person(input_file)}-{output_endname}-{file_index}.csv"
    output_path = os.path.join(output_folder, output_name)

    try:
        final_df.to_csv(output_path, sep=';', index=False)
        logging.info(f"Processed {input_file} -> {output_path} (kept {len(final_df)} rows)")
    except Exception as e:
        logging.error(f"Failed writing output CSV {output_path}: {e}")

def move_file_to_archive(
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