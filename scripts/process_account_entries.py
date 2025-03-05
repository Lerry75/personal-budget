import os
import logging
import glob
from utils.config_loader import load_config
from utils.category_map import load_category_rules
from utils.input_file_wrapper import get_df_from_csv_nordea
from utils.entries_processor import load_category_model, categorize_entries, write_output_files, move_file_to_archive

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    use_ml_model = [False]
    paths = load_config('config.yaml', use_ml_model)

    # Load ML model or category rules
    key_file = {True: 'model_file', False: 'category_file'}[use_ml_model[0]]
    loader = {True: load_category_model, False: load_category_rules}[use_ml_model[0]]
    resource = loader(paths[key_file])
    logging.info(f"{paths[key_file]} loaded.")

    processed_file_no = 0
    csv_files = glob.glob(os.path.join(paths['input_folder'], "*.csv"))
    for index, csv_file in enumerate(csv_files):
        try:
            entries = get_df_from_csv_nordea(csv_file)
            categorize_entries(entries, resource)
            write_output_files(entries, csv_file, paths['output_folder'], index)
            move_file_to_archive(csv_file, paths['processed_folder'])
            processed_file_no += 1
        except Exception as e:
            logging.error(f"Failed to process {csv_file}: {type(e).__name__} - {e}")
            continue
        
    logging.info(f"{processed_file_no} file(s) processed.")

if __name__ == "__main__":
    main()
