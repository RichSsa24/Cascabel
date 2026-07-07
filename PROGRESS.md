# CASCABEL Progress

## Current Phase: Phase 1 (Lab + Orchestrator)
**Status**: Not Started

## Completed Phases
* Phase 0 (Scope, Audit, Repo)

## Open Questions
*None*

## Deviations & Reasons
* **Python 3.14 Compatibility**: Removed `pydantic` in favor of standard Python `dataclasses` because `pydantic-core` requires building a rust wheel which fails on the lab host without MSVC tools.
