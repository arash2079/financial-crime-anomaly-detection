# Data card

**Origin:** Original simulator in `pipeline.py`, seed 2079. Entirely artificial accounts, transfers and labels. No banking export, customer identifiers or employer data. Data generation and processing do not require external services. CAD is the only represented currency.

**Size:** 37,320 events, 240 accounts, 60 days beginning 2026-01-01. 2,520 positive-pattern events (6.75%). Benchmarks use chronological 36/12/12-day splits. `metrics.json` records exact bounds, counts, versions and checksum. Separate demo seed 2080 generates 1,044 events over two days with its own checksum.

**Normal generator:** Daily background transfers draw variable account-level log-normal scales and a wide amount distribution. Additional legitimate payroll/hub fan-out and reimbursements create high-volume and rapid-transfer overlaps with suspicious patterns. Account roles change over time and are drawn from the same account pool for both labels.

**Positive-pattern generator:** Fan-in followed by rapid fan-out, approximate cycles, and fan-out bursts. Six episodes per day, seven events per episode, with overlapping amount distributions. Every transfer in a positive episode is labelled 1, including first transfers that cannot always be distinguished using past-only information. Label means membership in a generated pattern; it does not indicate an actual offense or an expert-adjudicated suspicious activity report. Fixed episode rates, durations and generation choices can produce simulator-specific artifacts.

**Limitations:** Not a representative bank population. Simplified time/risk/currency/account behavior. No demographics, geographic/payment rail attributes, sanctions signals, investigations, repeated confirmed offender histories, expert annotations or real-world feedback loops. No estimate of real financial-crime prevalence or detection accuracy can be derived. No external-data validation has been conducted. The two-day demonstration has a cold-start period with empty account histories.

**External roadmap:** IBM AML-Data is pending license/provenance review and a separate integration. No IBM or external results are claimed by this release. Dataset licenses must be tracked separately from this project's code license.

**Release policy:** Ship the original generator plus deterministic regenerated model/metrics/demo artifacts. Never add employer exports, real account transactions or personal information. Browser-upload examples should use synthetic records; upload is processed locally without transmission when integrated as designed.
