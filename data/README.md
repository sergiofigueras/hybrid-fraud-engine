# Synthetic Dataset

The training dataset is intentionally **generated locally rather than committed to Git**. This keeps the repository compact while preserving a fully reproducible data-generation process.

Create the default 50,000-row dataset with:

```bash
python -m training.generate_data --rows 50000 --seed 42
```

The command writes:

```text
data/transactions.csv
```

Retrain the model with:

```bash
python -m training.train --review-rate 0.05
```

The repository already includes a trusted, synthetic trained model at `artifacts/fraud_model.joblib`, so cloning, verification, CLI evaluation, API startup, and Docker execution do **not** require the CSV.

To generate a different dataset:

```bash
python -m training.generate_data \
  --rows 100000 \
  --seed 123 \
  --output data/transactions.csv
```

The data does not represent real customers, accounts, merchants, or transactions. The `is_fraud` column is a synthetic label created by the noisy hidden function in `training/generate_data.py`.
