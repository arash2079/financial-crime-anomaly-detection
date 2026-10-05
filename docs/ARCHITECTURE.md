# Architecture decision record

## ADR-001: Local browser inference

The first release trains models offline in Python and exports versioned JSON.
The deployed interface uses native ES modules and semantic HTML/CSS rather than
React. This change from the initial proposal eliminates frontend package/build
dependencies for the bounded research interface. It does not replace training
or inference with rules. The inference module is shared by the browser and Node
parity tests. There is no database, customer-data storage or inference API.

The primary agent owns the Site checkout, integration and deployment. Specialist
agents produce bounded ML research code and independent audit findings outside
the checkout. The GitHub portfolio receives the same source and compact model
artifacts through authenticated GitHub operations.

## ADR-002: Honest data provenance

IBM AML-Data is the planned external benchmark. Data acquisition and license
verification precede any IBM performance claim. An original seeded simulator
supports development, testing and the public interactive prototype. Prototype
results remain explicitly simulation-only until the external experiment runs.

## ADR-003: Reproducible evaluation

Feature computation uses strictly earlier timestamps, with timestamp groups
updated only after the whole group is scored. Temporal partitions and alert
budgets are frozen before final evaluation. Exported outputs are verified against
Python, and benchmark metrics come from executable evaluation artifacts.
