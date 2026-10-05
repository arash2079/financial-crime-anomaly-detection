# Independent audit — AML Radar v0.1

**Verdict:** No critical or high finding identified in the reviewed ML implementation and static interface sources. Suitable as a **simulation-only research prototype**, subject to completing integration/deployment checks. This is not certification of production security, regulatory compliance or real-world financial-crime effectiveness.

**Audit method:** Independent source inspection, actual Python/Node test execution, adversarial input probes and independent model retraining. The auditor did not implement or change the training or website code. Corrections were made by the implementation agents and retested independently. This report is a frozen snapshot; later source changes require appropriate re-verification.

## Scope and exclusions

Reviewed: original simulator, chronological feature computation, model training/export, generated metrics, full demo Python/JavaScript parity, schema/resource validation, CSV parsing, alert ranking, label handling, graph history, rendering sinks, worker and optional WebMCP error handling.

Not executed: browser visual or end-to-end interaction, accessibility audit, real deployed network inspection, hosting header/CSP checks, GitHub CI execution, credential/permission review, package vulnerability scan, external IBM dataset evaluation, probability calibration, distribution-shift evaluation or multiple-seed uncertainty experiments. At snapshot time, the final Site asset assembly/identity had not been verified; ML origin artifacts and interface sources were audited separately. Browser-only privacy claims below describe inspected source behavior, not observed browser network traffic.

## Executed evidence

| Check | Actual observed result |
|---|---|
| `python -m unittest -v test_pipeline` in ML workspace | PASS: 11 tests, including timestamp ties, equivalent instants, future/label/ID/account rename invariance, window boundaries, deterministic generation, cent precision, invalid evaluation and extreme-expiry regression |
| `node test_parity.mjs` in ML workspace | PASS: all 1,044 demo rows; 14 causal/schema checks; 20,000-row hot-account stress; 10,001-row extreme expiry |
| Python ↔ JS maximum feature difference | 1.7763568394002505e-15, below declared 1e-10 tolerance |
| Python ↔ JS maximum LR score difference | 3.885780586188048e-16 |
| Python ↔ JS maximum RF score difference | 4.6629367034256575e-15 |
| Independent five-seed extreme-expiry probe | PASS: 9,999 large prior transfers expire while one CAD 0.01 transfer remains; exact `log1p(0.01)` retained for all five seeds |
| Independent CSV/ranking/label-metric probes | PASS: 25 assertions including quoted/escaped/BOM input, malformed/header/size/row errors, tied scores, ceil budget, partial/edited label N/A, no-positive recall N/A and invalid ranking input |
| Node syntax checks on app/core/worker modules | PASS |
| Independent dataset regeneration | PASS: 37,320 records and dataset SHA-256 match manifest; simulator and causal-feature source hashes match |
| Independent historical Random Forest retraining | PASS: entire exported forest and every held-out test metric match exactly |
| Independent historical Logistic Regression retraining | PASS: all test metrics exactly match; maximum parameter difference 4.4508841057222526e-13 under equivalent array layout, below 1e-10 tolerance |
| Narrow static secret-pattern scan | No matches for common GitHub/private-key/AWS/access-key patterns in reviewed source/artifact file types. This is not an exhaustive secret or history scan. |

The measured 20,000-row feature stress run took approximately **57.2 ms in Node** after optimization. This is a single local measurement, not a browser-device latency guarantee. The interface independently caps uploads at 5,000 rows and 5 MB and runs feature extraction/inference in a Web Worker.

## Findings and remediation

| ID | Severity | Finding | Final disposition |
|---|---|---|---|
| M1 | Medium | Python originally grouped same instants by timestamp string, allowing `Z` and `+00:00` forms to see each other's same-time history | RESOLVED: parsed-instant grouping; equivalent-instant regression passes; browser enforces canonical UTC forms |
| M2 | Medium | No-positive evaluation divided by zero; single-class ROC-AUC could emit NaN | RESOLVED: offline evaluation explicitly rejects empty/single-class windows; live no-positive recall displays N/A |
| M3 | Medium | Original JS hot-account history computation was quadratic; 20,000 valid rows took approximately 9.8 seconds | RESOLVED: queue heads, rolling aggregates and recipient multiplicities; independently retested around 57.2 ms; UI worker prevents synchronous inference blocking |
| M4 | Medium | First running-float optimization lost small remaining balances after large transfers expired; one seeded valid probe even produced a negative log total | RESOLVED: Python and JS aggregate exact integer cents, enforce at most two decimal places; independent five-seed extreme-expiry retest passes |
| M5 | Medium | Optional WebMCP execution originally returned apparent success when analysis caught a worker/inference error | RESOLVED BY SOURCE REVIEW: analysis returns result or null, clears score/result state on failure; tool throws on null. Browser fault injection remains unexecuted |
| L1 | Low | Failed analysis could leave old queue-count/graph-context text and `state.k`; detail edits could remain clickable during inference | Source robustness note communicated to project lead. Recheck final app and browser error/concurrency behavior; not a critical/high blocker for this prototype |
| R1 | Research limitation | Single simulator and main training seed; generator-specific patterns; no shifted/external dataset or confidence intervals | OPEN AND DISCLOSED: release must stay simulation-only |
| R2 | Research limitation | Balanced classifiers produce uncalibrated positive-label scores; Isolation Forest produces anomaly ranks | OPEN AND DISCLOSED: no calibrated crime-probability claim |

Cent aggregation is numerically bounded: at most 20,000 records × CAD 1e9 × 100 cents = 2e15, below JavaScript's exact-integer limit 2^53. Amount values with more than two decimal places must be rejected rather than silently rounded. Browser CSV parsing is followed by record-schema validation.

## ML protocol conclusions

- Training contains 22,392 rows; validation and final test each contain 7,464. Chronological boundaries are explicit. Historical context legitimately continues from past windows into later ones.
- At score time t, feature history is [t−86,400 seconds, t). Every equal-time group is scored before history updates. Labels, IDs and account strings are not numerical predictors. Account names index histories; consistent renaming preserves features.
- Scaler and supervised/unsupervised estimators fit training rows only. Hyperparameters are fixed; the website wording now matches this policy. Default forest choice must not be described as test-based champion selection.
- Shared accounts across windows support existing-account scoring. They do not demonstrate unseen-account or unseen-institution generalization.
- Results use **Average Precision**, not an interchangeable trapezoidal PR-AUC label. Alert budgets use ceil(n×fraction), stable chronological tie handling, and common frozen test rows.
- Historical forest test AP is 0.4185266103140224; historical LR AP is 0.14004262538473627; amount-rule AP is 0.09098722025983125; amount-only forest AP is 0.10310166892117167. These are measured simulator results only. A weak Isolation Forest result must remain visible rather than be omitted or represented as a superior model.
- Original labels mean planted generator-pattern membership, not actual financial crime or adjudicated suspicious activity. Initial transfers inside a planted episode may legitimately have no distinguishable prior signal.
- Graph display is transaction context, not a trained graph model or demonstrated cycle detector. Logistic contributions are conditional additive model log-odds terms, not causal explanations. Forest detail shows observed inputs without fabricated attribution.

## Interface/privacy/security conclusions from source inspection

- A persistent SIMULATION ONLY banner, explicit external-benchmark-pending status, uncalibrated-score caveat and model/data limitations appear in the interface.
- Unknown or partial labels produce N/A live evaluation metrics. Amount edits disable label metrics and recompute the chronology; the original frozen experiment artifact is separate.
- Historical graph filters use timestamps strictly before the selected transaction and include only the preceding 24 hours.
- Transaction IDs, account names, filenames and other variable text render through `textContent` or safe text nodes/SVG attributes; no untrusted HTML insertion found in the reviewed code.
- Fetches load bundled model/metrics/demo artifacts. No raw transaction upload, local persistence, database or inference API was found. The downloadable CSV uses trusted generated demo fields; uploaded account fields are not re-exported into a spreadsheet.
- File byte/row/cell/column bounds, quote parsing, header allowlists, canonical dates, unique IDs, positive finite CAD amounts, cent precision and string lengths constrain inputs. A file extension/MIME check is not used as the security boundary.
- Workers perform inference. Error-result semantics were inspected after remediation. Actual worker execution, cancellation, startup/failure behavior and user flow remain browser/E2E checks.

## Release gates

| Gate | Status |
|---|---|
| Causal ML features and training-only fit | PASS for reviewed simulator |
| Honest provenance and score interpretation | PASS by inspected metadata/cards/interface wording |
| Full exported demo inference parity | PASS, all 1,044 records |
| Reproducible dataset and principal LR/RF experiments | PASS with declared floating tolerance |
| Bounded CSV/ranking/label handling | PASS pure Node probes and source review |
| Final Site copy matches audited ML module/artifacts | PENDING integration identity check |
| Deployed artifact availability/content | NOT RUN by this auditor |
| Browser visual/E2E/accessibility/worker errors | NOT RUN |
| Vulnerability scan and hosting/network security | NOT RUN |
| External effectiveness, shifted data, calibrated probabilities | NOT ESTABLISHED; research follow-ups |

No production-ready or real-bank-accuracy claim is supported. Publication as a clearly labeled v0.1 simulation research prototype is compatible with these findings once assembled assets and deployment availability are checked, with unexecuted browser checks disclosed.

## Primary references for audit criteria

- scikit-learn temporal splits: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
- scikit-learn probability calibration: https://scikit-learn.org/stable/modules/calibration.html
- scikit-learn Average Precision: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html
- OWASP file upload controls: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- IBM AML-Data provenance and separate dataset licensing: https://github.com/IBM/AML-Data

## Snapshot identity

Generated at 2026-10-05T14:01:45.262121+00:00 UTC.

Dataset SHA-256: `60e8a32666d758db8ba70181a3ffaf51774d32f7f5bda77acb26fe1b54ad1713`.

| Reviewed file | SHA-256 |
|---|---|
| `ml/pipeline.py` | `7d8765a5cb2b11186705a3b7dff492f83b18b174273930483a309797ad87f51e` |
| `ml/inference.mjs` | `358d563506b960e6367eca2bb49c789c138516ecc353177481d21d01115c361b` |
| `ml/test_pipeline.py` | `e22fad5eb254f579a0ba410930de4cd16c7d8cc2ed051f7ee4c66618c4bb1ad5` |
| `ml/test_parity.mjs` | `a13ec914607226a5e7dd4914da8fa036677373eb83dad208426f9b2f4697beda` |
| `ml/requirements.txt` | `37d25cd77b87c89e00af5b03238de7c03f15159335b36c24ee4c9d256a264f44` |
| `ml/artifacts/models.json` | `d9407cc22049721c5b613746082f12f329d2957db0ca5c40db22f1b0b9e679bd` |
| `ml/artifacts/metrics.json` | `63be62d8a1f488c2c501d93cbffec4a1b0a10657378dda74bc00255ba27796ef` |
| `ml/artifacts/demo.json` | `379e41b00d951d93babca076561f62b52bbdfef1085ba7480f4373e6c9b6f316` |
| `ml/artifacts/parity-fixture.json` | `9de0521aa465e8fedf59f1f2bcbb97f7f49e99832551bbe7da4a2d69736cd2b0` |
| `site/app.mjs` | `e9ceb11a2ff8a24a4a2baf073c8332e17d51e97f1253b867a51df35d630623b3` |
| `site/lab-core.mjs` | `95f6803d8ee8d5bbad223c47badb94c672450b0fef91b58de7ef01cc3c9cf28c` |
| `site/inference-worker.mjs` | `66d48e84f2aaf7bad2ca02d8410ed44e20127ad4baca8684fab6cac8976de074` |
| `site/index.html` | `ead4ff9a70ca520be7bfea3c2bdbeb3dd52b7a5412b3a249ed18ec1b4a85019e` |
