# Phase 1 — Evaluation Report

**Enterprise Intrusion Prevention System (IPS)**
Consolidated results from data preparation through full pipeline integration.

---

## 1. Data Quality (Member 1)

**Source:** CICIDS2017 (MachineLearningCVE — pre-extracted flow features)

**Raw dataset:** 2,830,743 records across 8 capture files (Monday–Friday, various attack scenarios)

**Class merging and filtering applied:**
- DoS Hulk / GoldenEye / slowloris / Slowhttptest → merged into `DoS`
- FTP-Patator / SSH-Patator → merged into `BruteForce`
- Web Attack (Brute Force/XSS/SQLi), Infiltration, Heartbleed → dropped (all under 1,600 samples, insufficient to train on)

**Final class distribution (2,828,516 records after filtering):**

| Class | Records | % of total |
|---|---|---|
| BENIGN | 2,273,097 | 80.36% |
| DoS | 252,661 | 8.93% |
| PortScan | 158,930 | 5.62% |
| DDoS | 128,027 | 4.53% |
| BruteForce | 13,835 | 0.49% |
| Bot | 1,966 | 0.07% |

**Cleaning:** 2,867 rows dropped due to NaN/infinite values (produced by a small number of flow-rate calculations where duration was 0).

**Known limitation:** The MachineLearningCVE version of CICIDS2017 does not include real source IP addresses (they are anonymized in the flow-feature CSVs). Source IPs were synthetically simulated (500 unique addresses, later increased for testing) by hashing flow characteristics per row. This enables demonstration of blocking behavior but means IP-based decisions do not reflect real network topology — a limitation to state plainly in the report, not a flaw to hide.

**Split:** 80/20 train/test, stratified by class (2,260,519 train / 565,130 test rows).

---

## 2. Detection Model Quality (Member 2)

**Architecture:** Hybrid detection — XGBoost (supervised, known attack classification) + Isolation Forest (unsupervised, trained only on BENIGN traffic, catches anomalous/unknown patterns)

**Classifier results (XGBoost, evaluated on 565,130 held-out test rows):**

- **Overall accuracy: 99.91%**

| Class | Precision | Recall | F1-score | Support |
|---|---|---|---|---|
| BENIGN | 1.00 | 1.00 | 1.00 | 454,264 |
| Bot | 0.83 | 0.76 | 0.80 | 391 |
| BruteForce | 1.00 | 1.00 | 1.00 | 2,766 |
| DDoS | 1.00 | 1.00 | 1.00 | 25,605 |
| DoS | 1.00 | 1.00 | 1.00 | 50,343 |
| PortScan | 0.99 | 1.00 | 1.00 | 31,761 |

**Weakest class:** Bot (precision 0.83, recall 0.76) — expected, given it's the smallest class in the training data (1,966 total samples, ~391 in test). Worth stating directly in the report as a data-availability limitation rather than a modeling failure.

**Anomaly detector (Isolation Forest):**
- Trained exclusively on BENIGN traffic to learn a baseline of "normal"
- Anomaly threshold derived empirically from the 5th percentile of BENIGN scores on training data (−0.552), not a fixed guess — matches the model's `contamination=0.05` assumption
- Flagged 9.97% of test traffic as anomalous
- **Independently caught 30.26% of real attacks** — meaning nearly a third of attacks would have been flagged even without the classifier's help, supporting the case for a hybrid approach over a single-model system

---

## 3. Prevention Effectiveness (Member 3)

**Scoring approach:** `risk_score = model confidence × attack severity weight`, with a separate rule for anomaly-flagged BENIGN traffic (elevated caution without hardcoding severity).

**Results on a 50,000-row test sample (final, tuned run):**

| Class | Allowed | Blocked | Block rate |
|---|---|---|---|
| BENIGN | 31,584 | 8,523 | 21.2% |
| Bot | 9 | 11 | 55.0% |
| BruteForce | 0 | 248 | 100% |
| DDoS | 0 | 2,252 | 100% |
| DoS | 5 | 4,557 | 99.9% |
| PortScan | 7 | 2,804 | 99.75% |

**Tuning finding:** Initial severity weights under-weighted PortScan (0.5) and Bot (0.7), causing `risk_score` to consistently land just under the 0.75 block threshold even at near-perfect model confidence (~0.95–1.0). Recalibrating PortScan to 0.8 and Bot to 0.8 raised PortScan's block rate from 15% to 99.75%, with negligible cost elsewhere. This is a concrete, evidence-based tuning story for the report.

**False positive analysis:** The 21.2% BENIGN block rate is driven almost entirely by the IP-simulation design — once a synthetic IP is flagged for one malicious record, all traffic (including unrelated benign traffic) sharing that same synthetic IP within the 60-minute blocklist window is also blocked. This is a direct consequence of simulating IPs on a dataset that doesn't include real ones, and is a documented, explainable limitation rather than a scoring-logic defect.

**Repeat-offender enforcement:** Once an IP is blocked, subsequent traffic from it is blocked automatically without needing to re-run the model — demonstrated directly and is the core mechanism that makes this a prevention system, not just a detection system.

---

## 4. System Performance (Member 4)

**Pipeline:** Sequential per-record processing — preprocessing → detection (XGBoost + Isolation Forest) → scoring → blocklist check → SQLite logging.

**Final run (50,000 records, tuned configuration):**
- Total time: 1,306.16 seconds (~21.8 minutes)
- Throughput: 38.3 records/second
- Allowed: 31,605 | Blocked: 18,395
- Anomaly-flagged: 5,023 (10.0%)

**Known bottleneck:** Per-record model inference (not database I/O — an earlier connection-per-row inefficiency was identified and fixed by reusing a single SQLite connection with periodic commits). Remaining throughput limit is inherent to row-by-row prediction rather than batched inference.

**Documented as future work rather than fixed now:** batching predictions across multiple rows at once would substantially increase throughput — reasonable to state as a known optimization path in the report's "Limitations and Future Scope" section.

---

## 5. Summary for the Report

**What this demonstrates:**
- A working hybrid ML detection pipeline (XGBoost + Isolation Forest) achieving 99.91% classification accuracy
- Genuine prevention behavior — not just alerting, but active, persistent IP blocking with automatic repeat-offender enforcement
- An empirically tuned scoring system, with a real before/after improvement (PortScan block rate 15% → 99.75%) driven by data, not guesswork
- End-to-end throughput measurement on real data (38.3 records/sec on 50,000 rows)

**Honest limitations to state upfront (strengthens rather than weakens the report):**
1. Source IPs are simulated, not real — the dataset provides no IP field
2. Simulated-IP collisions inflate the false-positive rate on BENIGN traffic (21.2%) beyond what a system with real, unique per-flow IPs would likely show
3. Bot classification is weaker than other classes due to limited training samples (1,966 total)
4. Per-record inference limits throughput; batching is a known, unimplemented optimization

---

## 6. What's Left

- Traffic replay simulator (for a live-feeling demo)
- Dashboard (visual display of the numbers above)
- Full written report sections (introduction, methodology, literature survey, etc.) built around this evaluation
- Viva preparation
