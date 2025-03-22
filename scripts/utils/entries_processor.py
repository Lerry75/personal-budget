import os
import sys
import shutil
import pandas as pd
import logging
import joblib
import csv
from datetime import datetime
from utils.utils import get_person
from utils.dataset_enricher import enrich_dataframe, get_feature_list
from utils.category_map import categorize_row

def categorize_entries(df_dict: { pd.DataFrame, pd.DataFrame }, resource: any):
    if type(resource) is list:
        categorize_entries_re(df_dict, resource)
    else:
        categorize_entries_ml(df_dict, resource)

def categorize_entries_re(df_dict: { pd.DataFrame, pd.DataFrame }, category_rules: list):
    df_dict['expenses']['Category'] = df_dict['expenses'].apply(lambda row: categorize_row(row, category_rules), axis=1)
    df_dict['income']['Category'] = df_dict['income'].apply(lambda row: categorize_row(row, category_rules), axis=1)

def categorize_entries_ml(df_dict: { pd.DataFrame, pd.DataFrame }, model):
    for key in df_dict.keys():
        if key == "expenses":
            enrich_dataframe(df_dict[key])
            features = df_dict[key][get_feature_list()]

            # Predict Categories
            try:
                df_dict[key]['Category'] = model.predict(features)
            except Exception as e:
                logging.error(f"Error during prediction: {e}")
        else:
            df_dict[key]['Category'] = None

def load_category_model(model_file: str):
    logging.info(f"Loading ML model from '{os.path.relpath(model_file)}'...")
    try:
        model = joblib.load(model_file)
        logging.info(f"ML model successfully loaded.")
        return model
    except Exception as e:
        logging.error(e)
        sys.exit(1)

def write_output_files(df_dict: { pd.DataFrame, pd.DataFrame },
    input_file: str,
    output_folder: str,
    file_index: int):

    # Select final columns
    final_cols = ["Year", "Month", "Amount DKK", "Category", "Person", "Type", "Notes"]

    for key in df_dict.keys():
        # Keep only columns that exist
        final_cols = [c for c in final_cols if c in df_dict[key].columns]
        final_df = df_dict[key][final_cols].copy()

        # Writes output CSV: '{Type}-{Person}-{yyyy}{MM}{dd}-{hh}{mm}-{index}.csv'
        output_endname = datetime.now().strftime("%Y%m%d-%H%M")
        output_name = f"{key}-{get_person(input_file)}-{output_endname}-{file_index}.csv"
        output_path = os.path.join(output_folder, output_name)

        try:
            final_df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
            logging.info(f"Processed '{os.path.relpath(input_file)}' -> '{os.path.relpath(output_path)}' (total {len(final_df)} rows).")
        except Exception as e:
            logging.error(f"Failed writing output CSV {output_path}: {e}")

def write_output_file(transactions: list, input_file:str, output_folder: str, file_index: int):
    """
    Writes the transactions to a CSV file with the specific output filename convention.
    The CSV uses a semicolon as separator and no text qualifiers.
    """
    output_endname = datetime.now().strftime("%Y%m%d-%H%M")
    output_filename = f"cardentries-{get_person(input_file)}-{output_endname}-{file_index}.csv"
    output_filepath = os.path.join(output_folder, output_filename)

    fieldnames = ["Booking date", "Title", "Amount"]
    try:
        with open(output_filepath, "w", newline='', encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
            writer.writeheader()
            writer.writerows(transactions)
        logging.info(f"Processed '{os.path.relpath(input_file)}' -> '{os.path.relpath(output_filepath)}' (total {len(transactions)} rows).")
    except Exception as e:
        logging.error(f"Failed writing output CSV {output_filepath}: {e}")

def move_file_to_archive(
    input_file: str,
    output_folder: str
):
    try:
        file_name = os.path.basename(input_file)
        destination = os.path.join(output_folder, file_name)

        shutil.move(input_file, destination)
        logging.info(f"File moved to '{os.path.relpath(destination)}'.")
    except FileNotFoundError:
        logging.error("Error: The file '{input_file}' does not exist.")
    except Exception as e:
        logging.error(f"Error: {str(e)}")

def assign_years(transactions: list) -> list:
    """
    Updates each transaction's 'Booking date' to include the year.
    - If only one month is present, all transactions get the current year.
    - If the two months are {12, 01}, then transactions in January get the current year
      and those in December get the previous year.
    - Otherwise, assume all transactions belong to the current year.
    """
    current_year = datetime.now().year
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