# CASCABEL
An AI-assisted, authorization-first purple-team platform.

## Overview
CASCABEL closes the detection-engineering loop automatically. It safely emulates benign adversary techniques, captures the telemetry those techniques generate, uses AI to synthesize a Sigma detection rule grounded strictly in that telemetry, and mathematically proves the rule works against the telemetry.

## Features (Phases 0-5 Complete)
* **Phase 0 (Auth/Ledger)**: A strictly enforced Ed25519-signed scope and an immutable JSONL audit ledger.
* **Phase 1 (Lab & Orchestrator)**: Safe, Python-based test runner that ensures all emulations are benign, reversible, and correctly logged.
* **Phase 2 (Telemetry)**: Automated collection and time-window correlation of emulated activity (e.g. process executions).
* **Phase 3 (AI Synthesis)**: Grounded, mathematically proven detection engineering using local LLMs (or offline deterministic mocks), verified by `pySigma`.
* **Phase 4 (Coverage Optimizer)**: A submodular greedy optimizer to recommend the next best technique to emulate to maximize MITRE ATT&CK coverage.
* **Phase 5 (Dashboard & PDF)**: A full React/Vite/Tailwind frontend (`cascabel serve`) for visualizing coverage heatmaps, the immutable ledger, and generated detections. Plus, an executive PDF generator (`cascabel report`).

## Usage

### Local Environment
1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. Generate keys & scope: `cascabel generate-keys`, edit `scope.yaml`, `cascabel sign-scope scope.yaml cascabel.key`
4. Run agent in background: `python -m target.agent`
5. Run the optimizer: `cascabel optimize`
6. Emulate: `cascabel run T1059.004`
7. Correlate: `cascabel correlate T1059.004`
8. Synthesize: `cascabel synthesize T1059.004`
9. Prove: `cascabel prove T1059.004`
10. Dashboard: `cd frontend && npm run build`, then `cascabel serve` and open `http://localhost:8888`.
11. Report: `cascabel report`

### Docker (Production Ready)
```bash
# Build the frontend first (requires Node.js)
cd frontend && npm install && npm run build && cd ..

# Launch the full stack
docker compose up -d --build
```
Open `http://localhost:8888` for the Dashboard.

## Constraints & Honesty
This platform was built adhering to strict non-negotiable constraints (`C0` - `C6`), ensuring authorization first, benign-only testing, offline/OSS capability, and absolute mathematical grounding in telemetry for every generated detection.
