import pandas as pd

def get_feature_list() -> list:
    return ['Notes', 'Person', 'Amount', 
            'MonthNumber', 'Year', 'IsBirthdayMonth', 
            'IsXmasMonth', 'IsSummerMonth', 'IsSchoolHolidayMonth']

def get_text_feature() -> str:
    return "Notes"

def get_numeric_features() -> list:
    return ['Amount', 'Year', 'MonthNumber', 'IsBirthdayMonth', 
            'IsXmasMonth', 'IsSummerMonth', 'IsSchoolHolidayMonth']

def get_categorical_features() -> list:
    return ["Person"]

def get_target_label() -> str:
    return 'Category'

def enrich_dataframe(df: pd.DataFrame):
    month_map = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
        'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    df['MonthNumber'] = df['Month'].map(month_map)
    if df['Amount'].dtype == object:
        df['Amount'] = df['Amount'].str.replace(',', '.').astype(float)
    df['IsBirthdayMonth'] = ((df['Month'] == 'Jan') | 
                             (df['Month'] == 'Mar') | 
                             (df['Month'] == 'Oct') | 
                             (df['Month'] == 'Nov') | 
                             (df['Month'] == 'Dec')).astype(int)
    df['IsXmasMonth'] = (df['Month'] == 'Dec').astype(int)
    df['IsSummerMonth'] = (df['Month'] == 'Jul').astype(int)
    df['IsSchoolHolidayMonth'] = ((df['Month'] == 'Feb') | (df['Month'] == 'Oct')).astype(int)