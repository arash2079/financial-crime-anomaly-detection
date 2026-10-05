# Transaction anomaly detection: executable research prototype

This is a CPU-trained, original **synthetic-data** proof of concept. It asks whether strictly historical transaction features improve alert ranking compared with an amount-only baseline at a fixed review capacity. It does not detect or prove financial crime in real customers. No TD, employer, or customer data is used. IBM AML-Data is a future validation target; it has **not** been downloaded, trained on, or evaluated here.

## Reproduce

Verified environment: Python 3.12.14 and Node 24.19.0. Runtime dependencies are pinned in `requirements.txt`. Training requires no network, GPU, paid API or external dataset.

```bash
python -m pip install -r requirements.txt
python pipeline.py
python -m unittest -v
node test_parity.mjs
```

The seed is 2079. Training writes `artifacts/models.json`, `metrics.json`, `demo.json`, and `parity-fixture.json`. The last file is a full Python reference for every feature and LR/RF score in the browser scenario. The dataset is regenerated, rather than shipped as a second large data file. Metadata records dataset SHA-256, simulator and feature function hashes, environment versions and exact split bounds.

## Experimental design

37,320 transactions over 60 days comprise 34,800 benign and 2,520 synthetic-pattern labels. Train: first 36 days, validation: next 12 days, test: last 12 days. Each split is chronological; there is no random splitting. All preprocessing and model fitting use only the training split. Validation metrics are reported; no validation-driven hyperparameter search was performed. Test results were not used to choose hyperparameters. The classifier settings were fixed before evaluation. Earlier transactions remain available as history across split boundaries because chronological history would be available at deployment. Labels, transaction IDs, account IDs and future events are excluded as numerical predictors. Same-time events are scored before any member of that timestamp group updates history.

Comparisons: descending-amount rule; amount-only versus historical Logistic Regression, Random Forest, and Isolation Forest. LR uses training-fitted standardization and balanced class weights; RF uses 32 trees, maximum depth 8, leaf minimum 12, balanced class weights; Isolation Forest uses 32 trees with 256 training samples per tree. LR maximum iterations: 500. Isolation Forest is fitted without labels. Its reversed normality score ranks anomalies but is not a probability. Browser exports include only historical LR and RF.

Average precision (AP) is the primary class-imbalance-sensitive ranking measure; ROC-AUC is also reported. For 1%, 5%, 10% review budgets, rank scores descending, preserve chronological order for ties, and review `ceil(n * budget)` rows. Precision is true positives / reviewed; recall is true positives / all positives. Evaluation refuses empty or single-class label windows to avoid undefined ROC/recall. The interactive UI can evaluate additional budgets on the demonstration scenario, but those numbers are separate from this frozen test benchmark.

## Measured test results

| Model | Average precision | ROC-AUC | Precision at 5% | Recall at 5% |
|---|---:|---:|---:|---:|
| Amount rule | 0.091 | 0.644 | 4.0% | 3.0% |
| Amount-only LR | 0.091 | 0.644 | 4.0% | 3.0% |
| Amount-only RF | 0.103 | 0.652 | 12.3% | 9.1% |
| Amount-only Isolation Forest | 0.050 | 0.377 | 2.9% | 2.2% |
| Historical LR | 0.140 | 0.716 | 18.7% | 13.9% |
| Historical RF | 0.419 | 0.789 | 50.5% | 37.5% |
| Historical Isolation Forest | 0.073 | 0.555 | 3.7% | 2.8% |

The frozen test window contains 7,464 rows, 504 positives (6.75%). At 5%, historical RF reviews 374 rows and retrieves 189 positives. Historical information improves supervised ranking **on this simulator**. Isolation Forest performs poorly here; it should not be marketed as an effective AML detector. No uncertainty intervals, multi-seed experiments, distribution-shift tests or external validation have been completed. Their absence limits generalization claims.

## Browser integration

```js
import {buildFeatures, scoreRow, scoreRecords, logisticContributions} from './inference.mjs';
const features = buildFeatures(demo.records);
const scores = scoreRecords(demo.records, exportedModels, 'forest');
const lrExplanation = logisticContributions(features[100], exportedModels.models.logistic);
```

Model keys are `logistic` and `forest`. `scoreRow(features, model)` returns a 0–1 **synthetic-label model score**, not a calibrated probability of financial crime. The LR contribution is exact log-odds contribution relative to standardized mean; it is not causal explanation. RF receives float32 features to match sklearn threshold inference. RF displays can show observed historical indicators; do not present those indicators as signed tree explanations or SHAP values.

The demo uses seed 2080 and includes all 1,044 events of a separate self-contained two-day scenario, starting from empty history. It is not the test dataset. If the UI changes a transaction or adds one, it must recompute the full chronological feature sequence and all model scores. Filtering for presentation must happen after scoring; otherwise filtering silently changes history. CSV ingestion must include relevant earlier history and valid UTC dates, positive finite CAD amounts with at most two decimal places, unique IDs and distinct sender/receiver. The native JS validator permits 1–20,000 rows and optional labels. Model scoring does not consume labels. History totals use exact integer cents, avoiding floating-point cancellation during window expiry; a 10,001-row large-value regression verifies a one-cent remainder.

See [FEATURE_CONTRACT.md](FEATURE_CONTRACT.md), [DATA_CARD.md](DATA_CARD.md) and [MODEL_CARD.md](MODEL_CARD.md) for exact scope and constraints.
