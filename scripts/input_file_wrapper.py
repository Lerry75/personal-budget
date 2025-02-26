import os
import pandas as pd
import logging
from utils import parse_amount, get_person, format_amount

def get_df_from_csv_nordea(input_file: str) -> { pd.DataFrame, pd.DataFrame }:
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
    expenses = df[df["Amount_float"] < 0]
    expenses["Amount_float"] = expenses["Amount_float"].abs()

    return { "income": income, "expenses": expenses }