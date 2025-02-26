import os
import sys
import shutil
import pandas as pd
import logging
import joblib
from datetime import datetime
from utils import get_person
from dataset_enricher import enrich_dataframe, get_feature_list
from category_map import categorize_row

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
    try:
        model = joblib.load(model_file)
        logging.info(f"Loaded ML model from {model_file}")
        return model
    except Exception as e:
        logging.error(e)
        sys.exit(1)

def write_output_files(df_set: { pd.DataFrame, pd.DataFrame },
    input_file: str,
    output_folder: str,
    file_index: int):

    # Select final columns
    final_cols = ["Year", "Month", "Amount DKK", "Category", "Person", "Type", "Notes"]

    for key in df_set.keys():
        # Keep only columns that exist
        final_cols = [c for c in final_cols if c in df_set[key].columns]
        final_df = df_set[key][final_cols].copy()

        # Writes output CSV: '{Type}-{Person}-{yyyy}{MM}{dd}-{hh}{mm}-{index}.csv'
        output_endname = datetime.now().strftime("%Y%m%d-%H%M")
        output_name = f"{key}-{get_person(input_file)}-{output_endname}-{file_index}.csv"
        output_path = os.path.join(output_folder, output_name)

        try:
            final_df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
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