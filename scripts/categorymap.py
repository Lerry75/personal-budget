import os
import re
import yaml

def load_category_rules(yaml_file: str) -> list:
     # Loads category classification rules from a YAML file.
    if not os.path.exists(yaml_file):
        raise ValueError(f"Category rules file not found: {yaml_file}")
    with open(yaml_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    rules = config.get('rules', [])
    if not rules:
        raise ValueError("No 'rules' key found in the YAML or it's empty.")
    return rules

def evaluate_condition(row, column, operator, value) -> bool:
    if column not in row:
        return False  # Column missing in data
    
    if str(column).lower() == "amount":
        column = str(column) + "_float"

    cell_value = row[column]

    # Apply the operator
    if operator == "contains":
        return str(value).lower() in str(cell_value).lower()
    elif operator == "equals":
        return str(cell_value).strip().lower() == str(value).strip().lower()
    elif operator == "startswith":
        return str(cell_value).strip().lower().startswith(str(value).strip().lower())
    elif operator == "endswith":
        return str(cell_value).strip().lower().endswith(str(value).strip().lower())
    elif operator == "regex":
        return re.search(str(value), str(cell_value), re.IGNORECASE)
    elif operator == "greater_than":
        try:
            return float(cell_value) > float(value)
        except ValueError:
            return False
    elif operator == "less_than":
        try:
            return float(cell_value) < float(value)
        except ValueError:
            return False
    return False

def categorize_row(row, rules) -> str:
    # Catecorize a single note against the loaded rules
    for rule in rules:
        conditions = rule.get("conditions", [])
        category = rule.get("category", "Uncategorized")

        # Check all conditions in the rule (AND logic)
        if all(evaluate_condition(row, cond['column'], cond['operator'], cond['value']) for cond in conditions):
            return category

    # Default category if no rules match
    return "Uncategorized"
