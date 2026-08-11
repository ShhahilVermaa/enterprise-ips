# Dataset

CICIDS2017 — MachineLearningCVE (pre-extracted flow features)
Download: https://www.unb.ca/cic/datasets/ids-2017.html

After downloading `MachineLearningCSV.zip`, unzip into `data/raw/`:
mkdir -p data/raw
unzip MachineLearningCSV.zip -d data/raw/

Expected: 8 CSV files, ~2.83M total records.
Class distribution and merge logic: see config.py (CLASS_LABELS, LABEL_MERGE_MAP)