import os
import sys
import logging
import glob
import pandas as pd
import joblib
from config_loader import load_config
from category_map import load_category_rules
from file_processor import process_input_file, categorize_expenses_re, categorize_expenses_ml, write_output_file, move_file_to_archive

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    use_ml_model = [False]
    paths = load_config('config.yaml', use_ml_model)

    # Load category rules
    if not use_ml_model[0]:
        try:
            rules = load_category_rules(paths['category_file'])
            logging.info(f"Loaded {len(rules)} category rules from {paths['category_file']}")
        except ValueError as e:
            logging.error(e)
            sys.exit(1)

    # Load ML model
    if use_ml_model[0]:
        try:
            model = joblib.load(paths['model_file'])
            logging.info(f"Loaded ML model from {paths['model_file']}")
        except ValueError as e:
            logging.error(e)
            sys.exit(1)

    processed_file_no = 0
    for index, csv_file in enumerate(glob.glob(os.path.join(paths['input_folder'], "*.csv"))):
        df = process_input_file(csv_file)
        if use_ml_model[0]:
            categorize_expenses_ml(df, model)
        else:
            categorize_expenses_re(df, rules)

        write_output_file(df, csv_file, paths['output_folder'], index)
        move_file_to_archive(csv_file, paths['processed_folder'])
        processed_file_no += 1

    logging.info(f"{processed_file_no} file(s) processed.")

if __name__ == "__main__":
    main()
