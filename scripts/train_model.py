import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.model_selection import GridSearchCV
import joblib
import os

def main():
    # Load historical expenses
    script_dir = os.path.dirname(os.path.abspath(__file__))
    training_file = os.path.join(script_dir, "..", "data", "training_data.csv")
    df = pd.read_csv(training_file, sep=';', encoding='ansi', dtype=str, keep_default_na=False)

    # Convert Amount to float
    df['Amount'] = df['Amount'].str.replace(',', '.').astype(float)

    # Prepare data
    X = df[["Notes", "Person", "Amount", "Month"]]
    y = df['Category']  # target label

    numeric_features = ["Amount"]
    numeric_transformer = StandardScaler()

    text_features = "Notes"
    text_transformer = TfidfVectorizer(lowercase=True, stop_words="english")

    categorical_features = ["Person", "Month"]
    categorical_transformer = OneHotEncoder(handle_unknown="ignore")

    # Combine them in a single ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ("text", text_transformer, text_features),
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop"  # drop other columns if any
    )

    # Use a RandomForest ensemble method, cross-validation, 
    # and Grid Search for Hyperparameter tuning
    rf = RandomForestClassifier(random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Build the final pipeline: ColumnTransformer + Voting
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("rf", rf)
    ])

    # Evaluate the pipeline with cross-validation - default Hyperparameters
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, X, y, cv=cv, scoring='accuracy', n_jobs=-1)
    
    print("Pipeline cross-validation accuracy scores:", scores)
    print("Mean accuracy:", scores.mean())

    # Hyperparameter Tuning with GridSearchCV
    # Define parameters to tune
    param_grid = {
        'rf__n_estimators': [100, 200],
        'rf__max_depth': [None, 10, 20],
        'rf__min_samples_split': [2, 5]
    }

    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring='accuracy',
        n_jobs=-1,
        verbose=2
    )

    grid_search.fit(X, y)

    print("Best params:", grid_search.best_params_)
    print("Best cross-validation accuracy:", grid_search.best_score_)

    # Evaluate the Best Model
    best_model = grid_search.best_estimator_
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train
    best_model.fit(X_train, y_train)

    # Evaluate
    y_pred = best_model.predict(X_test)

    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save the model
    model_path = os.path.join("models", "expense_categorizer_model.pkl")
    joblib.dump(best_model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    main()
