import os
import logging
import glob
from config_loader import load_config
from category_map import load_category_rules
from input_file_wrapper import get_df_from_csv_nordea
from entries_processor import load_category_model, categorize_entries_re, categorize_entries_ml, write_output_files, move_file_to_archive

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    use_ml_model = [False]
    paths = load_config('config.yaml', use_ml_model)

    # Load ML model or category rules
    if use_ml_model[0]:
        model = load_category_model(paths['model_file'])
    else:
        rules = load_category_rules(paths['category_file'])

    processed_file_no = 0
    for index, csv_file in enumerate(glob.glob(os.path.join(paths['input_folder'], "*.csv"))):
        entries = get_df_from_csv_nordea(csv_file)
        if use_ml_model[0]:
            categorize_entries_ml(entries, model)
        else:
            categorize_entries_re(entries, rules)

        write_output_files(entries, csv_file, paths['output_folder'], index)
        move_file_to_archive(csv_file, paths['processed_folder'])
        processed_file_no += 1

    logging.info(f"{processed_file_no} file(s) processed.")

if __name__ == "__main__":
    main()
