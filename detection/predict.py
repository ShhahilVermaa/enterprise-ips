# detection/predict.py

import os
import joblib
import pandas as pd

from config import MODEL_PATH, ANOMALY_MODEL_PATH
from common.schemas import TrafficFeatures, PredictionResult

LABEL_ENCODER_PATH = os.path.join(os.path.dirname(MODEL_PATH), "label_encoder.pkl")
ANOMALY_THRESHOLD_PATH = os.path.join(os.path.dirname(MODEL_PATH), "anomaly_threshold.txt")

_model = None
_anomaly_model = None
_encoder = None
_feature_columns = None
_anomaly_threshold = None


def _load_models():
    """Lazy-load all artifacts once, reused across calls."""
    global _model, _anomaly_model, _encoder, _feature_columns, _anomaly_threshold
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

        if not os.path.exists(ANOMALY_THRESHOLD_PATH):
            raise FileNotFoundError(
                f"{ANOMALY_THRESHOLD_PATH} not found — retrain with "
                f"'python -m detection.train_model' (old model artifacts detected)"
            )
        with open(ANOMALY_THRESHOLD_PATH) as f:
            _anomaly_threshold = float(f.read().strip())

    return _model, _anomaly_model, _encoder, _feature_columns, _anomaly_threshold


def predict(traffic: TrafficFeatures) -> PredictionResult:
    model, anomaly_model, encoder, feature_columns, anomaly_threshold = _load_models()

    row = pd.DataFrame([traffic.features], columns=feature_columns).fillna(0)

    pred_encoded = model.predict(row)[0]
    predicted_class = encoder.inverse_transform([pred_encoded])[0]
    confidence = float(max(model.predict_proba(row)[0]))

    anomaly_score = float(anomaly_model.score_samples(row)[0])
    is_anomaly = anomaly_score < anomaly_threshold

    return PredictionResult(
        predicted_class=predicted_class,
        confidence=confidence,
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
    )


if __name__ == "__main__":
    from config import SAMPLE_DIR

    sample_path = os.path.join(SAMPLE_DIR, "sample.csv")
    df = pd.read_csv(sample_path)
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