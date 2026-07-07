# Architectural Decisions Record (ADR)

## 1. Single Source of Truth Configuration
**Context**: Ports, IPs, and file paths were scattered as literals across `cli.py`, `agent.py`, and `docker-compose.yml`.
**Decision**: We introduced `cascabel.config.Config` to load all settings from environment variables with safe local defaults. All code must read `CONFIG` instead of raw `os.environ` or hardcoded literals.

## 2. LLM Provider Swappability
**Context**: We need to ensure the system defaults to a local OSS LLM (Ollama) to avoid paid APIs (Rule C4), but also allow testing without any network/model overhead.
**Decision**: Abstracted the LLM into `LLMProvider`. We have `OllamaProvider` (default) and `MockProvider`. Tests use the MockProvider for deterministic verification.

## 3. Strict Rule Grounding (C5)
**Context**: LLMs can hallucinate fields that were never observed in telemetry. 
**Decision**: We introduced `cascabel.synthesis.sigma_rule` which uses `pySigma` and custom parsing to evaluate the generated rule against the *exact* observed telemetry events. If the LLM generates an ungrounded rule, it is discarded or falls back to our deterministic generator.

## 4. Submodular Greedy Optimizer
**Context**: For Phase 4, we need an algorithm to select the next technique to emulate that maximizes MITRE ATT&CK coverage gain.
**Decision**: We use a greedy approach evaluating the marginal coverage gain of each technique against the currently emulated baseline.

## 5. Target Agent Subprocess Execution
**Context**: The benign target agent must execute atomic commands. Using `shell=True` in Python `subprocess` is a security anti-pattern.
**Decision**: We removed `shell=True` and instead pass the command explicitly via `["sh", "-c", command]` in Linux environments, ensuring the agent binds safely to the configured host.
