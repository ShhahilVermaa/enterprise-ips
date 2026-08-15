# detection/train_model.py

import os
import pandas as pd
from xgboost import XGBClassifier
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

from config import PROCESSED_DIR, MODEL_PATH, ANOMALY_MODEL_PATH, CLASS_LABELS

LABEL_COLUMN = "Label"
IP_COLUMN = "Source IP"
LABEL_ENCODER_PATH = os.path.join(os.path.dirname(MODEL_PATH), "label_encoder.pkl")


def load_split(name: str) -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, f"{name}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found — run 'python -m preprocessing.preprocess' first"
        )
    return pd.read_csv(path)


def split_features_labels(df: pd.DataFrame):
    X = df.drop(columns=[LABEL_COLUMN, IP_COLUMN])
    y = df[LABEL_COLUMN]
    return X, y


def train_classifier(X_train, y_train_encoded, encoder):
    print(f"Training XGBoost on {len(X_train):,} rows, {X_train.shape[1]} features...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=len(encoder.classes_),
        eval_metric="mlogloss",
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train_encoded)
    return model


def train_anomaly_detector(X_train, y_train):
    """Trained ONLY on BENIGN traffic -- learns what normal looks like."""
    print("\nTraining Isolation Forest on BENIGN traffic only...")
    benign_only = X_train[y_train == "BENIGN"]
    anomaly_model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42,
        n_jobs=-1,
    )
    anomaly_model.fit(benign_only)
    return anomaly_model


def train():
    print("Loading train/test data...")
    train_df = load_split("train")
    test_df = load_split("test")

    X_train, y_train = split_features_labels(train_df)
    X_test, y_test = split_features_labels(test_df)

    # XGBoost needs numeric labels -- encode string classes to ints
    encoder = LabelEncoder()
    encoder.fit(CLASS_LABELS)  # fixed order, consistent across runs
    y_train_encoded = encoder.transform(y_train)
    y_test_encoded = encoder.transform(y_test)

    model = train_classifier(X_train, y_train_encoded, encoder)

    print("\nEvaluating classifier on test set...")
    y_pred_encoded = model.predict(X_test)
    y_pred = encoder.inverse_transform(y_pred_encoded)

    acc = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {acc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))

    print("Confusion matrix (rows=true, cols=predicted):")
    labels_order = sorted(y_test.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels_order)
    print(pd.DataFrame(cm, index=labels_order, columns=labels_order))

    anomaly_model = train_anomaly_detector(X_train, y_train)

    print("\nEvaluating anomaly detector on test set...")
    anomaly_preds = anomaly_model.predict(X_test)  # -1 = anomaly, 1 = normal
    flag_rate = (anomaly_preds == -1).mean()
    print(f"Flagged {flag_rate:.2%} of test traffic as anomalous")

    actually_attack = (y_test != "BENIGN")
    flagged_anomaly = (anomaly_preds == -1)
    overlap = (actually_attack & flagged_anomaly).sum() / actually_attack.sum()
    print(f"Anomaly detector independently caught {overlap:.2%} of real attacks")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(anomaly_model, ANOMALY_MODEL_PATH)
    joblib.dump(encoder, LABEL_ENCODER_PATH)
    print(f"\nSaved: {MODEL_PATH}")
    print(f"Saved: {ANOMALY_MODEL_PATH}")
    print(f"Saved: {LABEL_ENCODER_PATH}")

    feature_columns_path = os.path.join(os.path.dirname(MODEL_PATH), "feature_columns.txt")
    with open(feature_columns_path, "w") as f:
        f.write("\n".join(X_train.columns))
    print(f"Saved: {feature_columns_path}")


if __name__ == "__main__":
    train()