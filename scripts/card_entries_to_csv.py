import os
import logging
import glob
from utils.config_loader import load_config
from utils.input_file_wrapper import parse_cc_statement_file
from utils.entries_processor import move_file_to_archive, write_output_file, assign_years

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    paths = load_config('config.yaml')

    logging.info("Starting conversion process.")
    processed_file_no = 0
    txt_files = glob.glob(os.path.join(paths['input_folder'], "*.txt"))
    for index, txt_file in enumerate(txt_files):
        try:
            transactions = parse_cc_statement_file(txt_file)
            transactions = assign_years(transactions)
            write_output_file(transactions, txt_file, paths['output_folder'], index)
            move_file_to_archive(txt_file, paths['processed_folder'])
            processed_file_no += 1
        except Exception as e:
            logging.error(f"Failed to convert {txt_file}: {type(e).__name__} - {e}")
            continue

    logging.info(f"{processed_file_no} file(s) converted.")

if __name__ == "__main__":
    main()
