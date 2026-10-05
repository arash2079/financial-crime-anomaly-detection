# Integration evidence — AML Radar v0.1

This report complements the frozen independent AUDIT.md; it does not alter the
auditor's snapshot or classify unexecuted browser checks as passed.

## Executed checks on assembled source

- Python unittest: 11 tests PASS.
- Node test runner: 12 tests PASS, including the actual inference-worker module
  executing through a Node worker-thread bridge.
- All 1,044 demo rows match Python LR/RF reference predictions within 1e-10.
- Maximum differences: feature 1.7763568394002505e-15; LR 3.885780586188048e-16;
  RF 4.6629367034256575e-15.
- Fourteen causal/schema checks, 20,000-row hot-account stress and 10,001-row
  extreme-cent-expiry regression PASS.
- Interface asset references and IDs exist; deployed and research JSONs and
  inference modules are byte-identical; modules pass syntax checks.
- Static checks found no untrusted HTML execution sinks or third-party scripts.

Low audit note L1 was corrected: failure resets alerts/queue/graph text and old
results, stops the worker and disables detail inputs while inference runs. Tool
calls reject failed analysis. UI branches were source-reviewed; actual worker
computational success/error/recovery was tested in the Node bridge.

## Unexecuted checks

Real-browser visual/E2E/accessibility and browser worker/CSP behavior remain
unverified. Plain static assets have no compatible managed-preview route here;
no substitute browser path was improvised. Optional WebMCP has no supported
permitted validation context. Deployed network/privacy behavior, hosting headers
and dependency vulnerability scanning were not executed.

## Source synchronization

Public GitHub repository `arash2079/financial-crime-anomaly-detection` exists. Initial writes returned HTTP 403 because the GitHub App selected only the earlier repository. On 5 October the owner added this project, and a successful tree/commit/ref write verified the correction. The charter and architecture commit is `2cdb9600bcc57e2a3379dad0dbf2b4af271a7d40`. Implementation is submitted through a feature branch and Pull Request. Remote CI status is reported after the actual run, separately from local tests.

This prepublication source report does not invent deployment or remote CI success;
GitHub Pages publication must be confirmed separately by its deployment run.

## Release scope

v0.1 simulation prototype with actual training/inference and measured experiments.
External IBM research benchmarking and browser checks are pending. This is not
the final externally validated admissions research release.

## Final source/CI evidence

GitHub Actions run 37322625050 completed successfully; verify job passed each Python/Node/parity step. PR #1 was merged as 6b95d7bb2a94c8b4fdf9359ff54a687ea33fe48d. Main app was read back and matches submitted source. These results validate the original implementation. See RELEASE.md for hosting status and preserved limitations.
