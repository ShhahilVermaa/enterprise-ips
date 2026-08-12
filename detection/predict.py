# detection/predict.py

import os
import joblib
import pandas as pd

from config import MODEL_PATH, ANOMALY_MODEL_PATH, ANOMALY_SCORE_THRESHOLD
from common.schemas import TrafficFeatures, PredictionResult

LABEL_ENCODER_PATH = os.path.join(os.path.dirname(MODEL_PATH), "label_encoder.pkl")

_model = None
_anomaly_model = None
_encoder = None
_feature_columns = None


def _load_models():
    """Lazy-load all three artifacts once, reused across calls."""
    global _model, _anomaly_model, _encoder, _feature_columns
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"{MODEL_PATH} not found — run 'python -m detection.train_model' first"
            )
        _model = joblib.load(MODEL_PATH)
        _anomaly_model = joblib.load(ANOMALY_MODEL_PATH)
        _encoder = joblib.load(LABEL_ENCODER_PATH)

        columns_path = os.path.join(os.path.dirname(MODEL_PATH), "feature_columns.txt")
        with open(columns_path) as f:
            _feature_columns = f.read().splitlines()

    return _model, _anomaly_model, _encoder, _feature_columns


def predict(traffic: TrafficFeatures) -> PredictionResult:
    """
    Takes a TrafficFeatures object, returns a PredictionResult.
    This is the contract Member 3 builds against.
    """
    model, anomaly_model, encoder, feature_columns = _load_models()

    row = pd.DataFrame([traffic.features], columns=feature_columns).fillna(0)

    pred_encoded = model.predict(row)[0]
    predicted_class = encoder.inverse_transform([pred_encoded])[0]
    confidence = float(max(model.predict_proba(row)[0]))

    anomaly_score = float(anomaly_model.score_samples(row)[0])
    is_anomaly = anomaly_score < ANOMALY_SCORE_THRESHOLD

    return PredictionResult(
        predicted_class=predicted_class,
        confidence=confidence,
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
    )


if __name__ == "__main__":
    import sys
    from config import SAMPLE_DIR

    sample_path = os.path.join(SAMPLE_DIR, "sample.csv")
    df = pd.read_csv(sample_path)

    # Get attack class from command line
    if len(sys.argv) > 1:
        requested_label = sys.argv[1]

        if requested_label not in df["Label"].unique():
            print(f"Label '{requested_label}' not found.")
            print("Available labels:")
            print(df["Label"].unique())
            raise SystemExit(1)

        matching_rows = df[df["Label"] == requested_label]

        if matching_rows.empty:
            print(f"No samples found for {requested_label}")
            raise SystemExit(1)

        row = matching_rows.iloc[0]

    else:
        # Default: first sample
        row = df.iloc[0]

    features = row.drop(labels=["Label", "Source IP"]).to_dict()

    traffic = TrafficFeatures(
        source_ip=row["Source IP"],
        features=features,
        true_label=row["Label"],
    )

    result = predict(traffic)

    print(f"True label: {traffic.true_label}")
    print(f"Predicted: {result.predicted_class} (confidence: {result.confidence:.3f})")
    print(f"Anomaly: {result.is_anomaly} (score: {result.anomaly_score:.3f})")