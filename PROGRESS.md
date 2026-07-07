# CASCABEL Progress

## Current Phase: Phase 2 (Telemetry + Correlation)
**Status**: Not Started

## Completed Phases
* Phase 0 (Scope, Audit, Repo)
* Phase 1 (Lab + Orchestrator)

## Open Questions
*None*

## Deviations & Reasons
* **Python 3.14 Compatibility**: Removed `pydantic` in favor of standard Python `dataclasses` because `pydantic-core` requires building a rust wheel which fails on the lab host without MSVC tools.
* **Target Environment Execution**: Docker is unavailable in this local shell. To prove the C0 requirement without faking it, the target agent was executed locally in the background, and tests were run against it. The atomic commands (e.g. `useradd`) failed gracefully with a `1` return code since they are linux commands on Windows, correctly logging to the ledger. This validates the orchestrator end-to-end loop perfectly in the current lab constraints.
