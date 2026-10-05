# AML Radar — Financial Crime Anomaly Detection

An interactive, reproducible **simulation-only research prototype** by Arash Amini.
Explore genuine trained-model inference, causal transaction history, measured
model comparisons and fixed-budget review queues. No TD/employer/customer data.

**Demo:** https://aml-radar-arash.arashamini.chatgpt.site

Not a production AML/compliance system. Scores are uncalibrated synthetic-label
outputs, not evidence or probabilities of crime. IBM data has not been evaluated.

## Research question

At a fixed review capacity, do strictly historical account features improve
ranking of planted suspicious-pattern transactions compared with amount alone?

## Interactive demo

Select a mixed or benign-only scene and a trained LR/RF model; change review
capacity, inspect ranked transfers and prior account context, edit amounts and
recompute chronology, or upload a bounded CAD CSV for local inference.
Methodology and Evaluation views explain the actual training and results.
The graph is context visualization, not a trained graph neural network.
Exact additive contributions are available for Logistic Regression only.

## Measured held-out results

Original simulator: 37,320 events, 60 days. Chronological train/validation/test:
22,392 / 7,464 / 7,464 rows. Settings fixed before evaluation. Separate demo:
1,044 events with independent seed.

| Model | Average Precision | ROC-AUC | Precision at 5% | Recall at 5% |
| --- | ---: | ---: | ---: | ---: |
| Amount-only RF | 0.103 | 0.652 | 12.3% | 9.1% |
| Historical LR | 0.140 | 0.716 | 18.7% | 13.9% |
| Historical RF | 0.419 | 0.789 | 50.5% | 37.5% |
| Historical Isolation Forest | 0.073 | 0.555 | 3.7% | 2.8% |

Simulator results only. All seven baselines/ablations, including weak results,
are in [metrics.json](research/artifacts/metrics.json). No uncertainty intervals,
multi-seed comparison, distribution-shift or external evaluation is complete.

## Reproduce

Verified Python 3.12.14 and Node 24.19.0; frontend has no npm dependencies.

```bash
python -m pip install -r research/requirements.txt
cd research
python pipeline.py
python -m unittest -v
cd ..
python scripts/sync-web-artifacts.py
npm test
npm run serve
```

Open http://localhost:8000. HTTP-serving is required for module workers;
opening index.html through file:// is unsupported. Models and data are regenerated
without a GPU, paid API or external dataset. The manifest records hashes,
versions, seed and exact split boundaries. Numeric tolerance is 1e-10.

## Structure and verification

| Path | Purpose |
| --- | --- |
| `research/` | Simulator, causal features, training/evaluation/exports and tests |
| `dist/` | Authored interface, model inference and compact JSON artifacts |
| `tests/` | CSV/ranking tests and actual worker execution in a Node bridge |
| `scripts/` | Artifact synchronization and static source/asset checks |
| `docs/` | Architecture, cards, contributions and audit reports |
| `.github/workflows/ci.yml` | Prepared CI workflow |

11 Python tests, 12 Node tests, 14 additional causal/schema checks and all
1,044-row Python-reference inference parity checks pass locally. Research and
deployed artifacts are byte-identical. Histories use exact integer cents.

[Independent audit](docs/AUDIT.md) and [integration evidence](docs/INTEGRATION.md)
record findings and corrections. Five medium findings were fixed. No critical/high
open issue was identified in reviewed source scope. Browser visual/E2E,
accessibility, hosting/network and dependency vulnerability checks were not run.
Node worker execution is not browser-rendering validation. Optional WebMCP
registration is feature-detected but supported-browser validation was unavailable.

The owner resolved initial integration access. Source is submitted through a reviewed feature branch. Local checks passed; the prepared GitHub Actions workflow will run after upload. Remote CI status is reported separately from local evidence.

## Licensing and contribution

Own code/fixtures: MIT. Libraries retain their terms. Future IBM data has separate
CDLA-Sharing-1.0 terms; no IBM data is included under this code license.
Read the [data card](docs/DATA_CARD.md), [model card](docs/MODEL_CARD.md),
[feature contract](docs/FEATURE_CONTRACT.md), and
[AI-assistance disclosure](docs/CONTRIBUTIONS.md).

## Next scientific milestone

Acquire the official [IBM AML-Data](https://github.com/IBM/AML-Data), verify its
version/license/schema, freeze temporal evaluation and repeat the comparison.
Then add repeated seeds, shift and entity-holdout tests. Graph models should
follow only as a justified measured comparison.

## Release evidence

[Release report](docs/RELEASE.md) records the successful GitHub Actions run, merged implementation and initial publication.
