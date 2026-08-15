# prevention/risk_scorer.py

from common.schemas import PredictionResult, Decision

from config import (
    MIN_CONFIDENCE_TO_ACT,
    RISK_BLOCK_THRESHOLD,
    ATTACK_SEVERITY_WEIGHTS,
)

from prevention.blocklist_manager import (
    is_blocked,
    add_to_blocklist,
)


def compute_risk_score(prediction: PredictionResult) -> float:
    """
    Calculate risk score using:

    risk_score = model confidence × attack severity
    """

    severity = ATTACK_SEVERITY_WEIGHTS.get(
        prediction.predicted_class,
        0.5
    )

    return prediction.confidence * severity


def score_and_decide(
    prediction: PredictionResult,
    source_ip: str
) -> Decision:
    """
    Main entry point for the Prevention Engine.

    Takes:
        PredictionResult + source IP

    Returns:
        Decision
    """

    # Rule 1: Already blocked IP → immediately BLOCK
    if is_blocked(source_ip):
        return Decision(
            risk_score=1.0,
            action="BLOCK",
            reason=f"IP {source_ip} is already on the blocklist",
        )

    # Rule 2: Low-confidence prediction → ALLOW
    if prediction.confidence < MIN_CONFIDENCE_TO_ACT:
        return Decision(
            risk_score=0.0,
            action="ALLOW",
            reason=(
                f"Low confidence ({prediction.confidence:.2f}), "
                "not acting on prediction"
            ),
        )

    # Rule 3: BENIGN traffic → ALLOW
    if prediction.predicted_class == "BENIGN":
        return Decision(
            risk_score=0.0,
            action="ALLOW",
            reason="Predicted BENIGN",
        )

    # Rule 4: Calculate risk score
    risk_score = compute_risk_score(prediction)

    # Rule 5: High risk → BLOCK
    if risk_score >= RISK_BLOCK_THRESHOLD:
        add_to_blocklist(source_ip)

        return Decision(
            risk_score=risk_score,
            action="BLOCK",
            reason=(
                f"Risk score {risk_score:.2f} >= threshold, "
                f"class={prediction.predicted_class}"
            ),
        )

    # Rule 6: Risk below threshold → ALLOW
    return Decision(
        risk_score=risk_score,
        action="ALLOW",
        reason=(
            f"Risk score {risk_score:.2f} below threshold, "
            f"class={prediction.predicted_class}"
        ),
    )


if __name__ == "__main__":

    from prevention.blocklist_manager import reset_blocklist

    reset_blocklist()

    # Test 1: High-confidence DDoS
    fake_ddos = PredictionResult(
        predicted_class="DDoS",
        confidence=0.95
    )

    decision1 = score_and_decide(
        fake_ddos,
        "10.0.1.1"
    )

    print(f"First DDoS from 10.0.1.1: {decision1}")

    # Test 2: Same IP again
    decision2 = score_and_decide(
        fake_ddos,
        "10.0.1.1"
    )

    print(f"Second attempt from same IP: {decision2}")

    # Test 3: Benign traffic
    fake_benign = PredictionResult(
        predicted_class="BENIGN",
        confidence=0.99
    )

    decision3 = score_and_decide(
        fake_benign,
        "10.0.2.2"
    )

    print(f"Benign traffic from 10.0.2.2: {decision3}")