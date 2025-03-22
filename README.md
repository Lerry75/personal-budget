# Personal Budget Manager

A Python-based tool for processing and categorizing bank account statements and credit card transactions. The tool processes CSV files from Nordea Netbank and TXT files from credit card statements, categorizes transactions, and generates organized output files.

## Features

- Process bank account statements (CSV files from Nordea Netbank)
- Process credit card statements (TXT files)
- Categorize transactions using predefined rules
- Generate organized output files with categorized transactions
- Support for both local and foreign currency transactions
- Automatic file archiving after processing
- Machine learning model for transaction categorization (optional)

## Project Structure

```
personal-budget/
├── config.yaml              # Configuration file with paths and settings
├── categoryrules.yaml       # Rules for transaction categorization
├── scripts/
│   ├── process_account_entries.py    # Process bank account statements
│   ├── card_entries_to_csv.py        # Process credit card statements
│   ├── train_model.py                # Train ML model for categorization
│   └── utils/
│       ├── config_loader.py          # Load configuration from YAML
│       ├── category_map.py           # Handle transaction categorization
│       ├── entries_processor.py      # Process and transform entries
│       ├── input_file_wrapper.py     # Parse input files
│       └── utils.py                  # Utility functions
├── data/                 # Training data for ML model
├── models/               # Trained ML models
├── input-csv/            # Place bank account CSV files here
├── input-card/           # Place credit card TXT files here
├── output-csv/           # Processed bank account files
├── output-card/          # Processed credit card files
├── processed-csv/        # Archived bank account files
└── processed-card/       # Archived credit card files
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/personal-budget.git
cd personal-budget
```

2. Create a Python virtual environment and activate it:
```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Unix/MacOS
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Processing Bank Account Statements

1. Place your Nordea Netbank CSV files in the `input-csv` directory
2. Run the processing script:
```bash
python scripts/process_account_entries.py
```

The script will:
- Process all CSV files in the input directory
- Categorize transactions using rules from `categoryrules.yaml` or ML model
- Generate output files in `output-csv`
- Move processed files to `processed-csv`

### Processing Credit Card Statements

1. Place your credit card TXT files in the `input-card` directory
2. Run the processing script:
```bash
python scripts/card_entries_to_csv.py
```

The script will:
- Process all TXT files in the input directory
- Convert transactions to a standardized format
- Generate output files in `output-card`
- Move processed files to `processed-card`

### Training the ML Model

The project includes a machine learning model for transaction categorization. To train or retrain the model:

1. Prepare your training data:
   - Place raw transaction data in `data/`
   - The data should be in CSV format with transaction descriptions and categories

2. Run the training script:
```bash
python scripts/train_model.py
```

The script will:
- Process the training data
- Train a new model
- Save the model to `models/expense_categorizer_model.pkl`

3. Enable ML model usage:
   - Set `use_ml_model: true` in `config.yaml`
   - The processing scripts will now use the ML model for categorization

## Configuration

### config.yaml
Main configuration file containing:
- Input/output directory paths
- File paths for categorization rules and ML models
- Application settings
  - `use_ml_model`: Enable/disable ML-based categorization

### categoryrules.yaml
Contains rules for categorizing transactions based on:
- Transaction descriptions
- Amount ranges
- Date patterns

## Output Format

### Bank Account Statements
Processed files include:
- Transaction date
- Amount
- Category
- Notes
- Person (account holder)
- Type (Actual/Transfer)

### Credit Card Statements
Processed files include:
- Transaction date
- Amount
- Description
- Currency (for foreign transactions)

## Logging

Both scripts provide detailed logging information:
- Processing start/end
- File processing status
- Errors and warnings
- Number of processed files

Logs are displayed in the console with timestamps and log levels.

## Error Handling

The scripts include robust error handling:
- File existence checks
- Format validation
- Amount parsing
- Date parsing
- Transaction categorization

Errors are logged but don't stop the entire process - other files continue to be processed.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
