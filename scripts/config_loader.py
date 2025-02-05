import os
import sys
import yaml
import logging

def load_config(config_file: str, use_ml_model: list) -> dict:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, '..', config_file)
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

    # Replacing wiwth absolute path
    for key in config['paths']:
        config['paths'][key] = os.path.join(script_dir, "..", config['paths'][key])

    setup_paths(config['paths'])

    # Load feature flag
    if 'app' in config:
        if 'use_ml_model' in config['app']:
            if config['app']['use_ml_model']:
                use_ml_model[0] = True

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