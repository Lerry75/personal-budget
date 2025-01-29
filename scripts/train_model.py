import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report
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
    X = df[["Notes", "Person", "Amount", "Year", "Month"]]
    y = df['Category']  # target label

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

    numeric_features = ["Amount", "Year"]
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

    # Use a VotingClassifier ensemble method.
    # It aggregates multiple base classifiers 
    # and the class with the highest average probability is selected (Soft voting).
    # Define base classifiers
    clf1 = LogisticRegression(random_state=42)
    clf2 = DecisionTreeClassifier(random_state=42)
    clf3 = RandomForestClassifier(n_estimators=100, random_state=42)
    clf4 = SVC(probability=True, random_state=42)

    # Create VotingClassifier
    voting_clf = VotingClassifier(
        estimators=[('lr', clf1), ('dt', clf2), ('rfc', clf3), ('svc', clf4)],
        voting='soft'
    )

    # Build the final pipeline: ColumnTransformer + Voting
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("voting", voting_clf)
    ])

    print("X_train shape:", X_train.shape)
    print("y_train shape:", y_train.shape)
    
    # Train
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save the model
    model_path = os.path.join("models", "expense_categorizer_model.pkl")
    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    main()
