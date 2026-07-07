# Antigravity Rules for CASCABEL

These seven rules are NON-NEGOTIABLE. They override speed, completeness, and impressiveness. If a request conflicts with one, follow the rule and say so.

## C0 — EXECUTE AND PROVE (Antigravity-native)
You genuinely execute — so you must, and you must produce verifiable evidence, not narration.
- Actually run every build step, test, and verification in the terminal. Drive Chrome to verify UI.
- Every completed task and phase must be backed by an Artifact (terminal output, screenshot, diff).
- Never assert a result you did not produce. If a check cannot run, label it UNVERIFIED.
- Use the Implementation Plan as the plan-of-record; Walkthrough/Verification for the end-to-end demo.

## C1 — AUTHORIZATION FIRST
Nothing that touches a target runs without a valid, non-expired, signed scope contract.
- `scope.yaml` (signed) declares limits. `dry_run` defaults to true.
- Signing is local, offline, free (Ed25519).
- Every action appends to a hash-chained audit ledger `ledger.jsonl`.
- Refuse any target outside the active scope.

## C2 — BENIGN ONLY
Orchestrate only benign, reversible, ATT&CK-mapped atomic tests.
- No offensive code, exploit, malware, C2, or credential theft.
- Every emulation has an explicit, tested cleanup/rollback.
- AI generates defensive artifacts only.

## C3 — SECURE, BUT FUNCTIONAL
Harden components to baselines without breaking required connections.
- Keep required internal flows functional. Run a connectivity smoke test after every security control addition.
- Never block a required port/service.
- Single-source configuration (`.env` + typed config).
- Safe local defaults out of the box.

## C4 — FREE AND OPEN-SOURCE ONLY
Every dependency, service, and tool must be free and open-source.
- Runtime LLM defaults to a local OSS model (Ollama). No paid APIs in runtime.
- Mock the runtime LLM in the test suite.
- Verify free/OSS status before adding.

## C5 — HONESTY & GROUNDING
Every factual claim traces to evidence.
- Detection rules reference only telemetry actually observed.
- If telemetry is insufficient, emit INSUFFICIENT_TELEMETRY.
- Metrics are lab-measured and labeled lab-scoped.
- Unbuilt work lives in Roadmap, not as fake badges.

## C6 — INTEGRITY
Nothing breaks anything else.
- Run the full test suite after every change and capture the result.
- No dependency conflicts.
- Phases follow dependency order.
