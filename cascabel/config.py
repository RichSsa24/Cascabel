"""Single-source configuration for CASCABEL (C3).

All hosts, ports, paths, and the runtime-LLM settings resolve here from
environment variables with safe local defaults, so a fresh clone boots
out of the box and no credential/host/port is duplicated across services.
Never read os.environ outside this module.
"""
import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value else default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    # Audit / auth artifacts
    ledger_path: str = "ledger.jsonl"
    scope_path: str = "scope.yaml"
    public_key_path: str = "cascabel.pub"
    private_key_path: str = "cascabel.key"

    # Telemetry store + mock collector sink
    db_path: str = "telemetry.db"
    mock_audit_log: str = "mock_audit.log"

    # Lab agent (the benign target). Bind to loopback by default so the
    # lab RCE endpoint is not exposed on all interfaces (C3).
    agent_host: str = "127.0.0.1"
    agent_bind: str = "127.0.0.1"
    agent_port: int = 8080

    # Data trees
    atomics_dir: str = "data/atomics"
    detections_dir: str = "data/detections"

    # Runtime LLM (C4): local OSS via Ollama by default; swappable + mockable.
    llm_provider: str = "ollama"
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "mistral"
    llm_timeout_s: int = 20

    # Detection synthesis refine loop cap (Phase 3).
    max_refine_iterations: int = 3

    # Dashboard/API
    api_host: str = "127.0.0.1"
    api_port: int = 8888


def load_config() -> Config:
    return Config(
        ledger_path=_env("CASCABEL_LEDGER_PATH", "ledger.jsonl"),
        scope_path=_env("CASCABEL_SCOPE_PATH", "scope.yaml"),
        public_key_path=_env("CASCABEL_PUBLIC_KEY", "cascabel.pub"),
        private_key_path=_env("CASCABEL_PRIVATE_KEY", "cascabel.key"),
        db_path=_env("CASCABEL_DB_PATH", "telemetry.db"),
        mock_audit_log=_env("CASCABEL_MOCK_AUDIT_LOG", "mock_audit.log"),
        agent_host=_env("CASCABEL_AGENT_HOST", "127.0.0.1"),
        agent_bind=_env("CASCABEL_AGENT_BIND", "127.0.0.1"),
        agent_port=_env_int("CASCABEL_AGENT_PORT", 8080),
        atomics_dir=_env("CASCABEL_ATOMICS_DIR", "data/atomics"),
        detections_dir=_env("CASCABEL_DETECTIONS_DIR", "data/detections"),
        llm_provider=_env("CASCABEL_LLM_PROVIDER", "ollama"),
        ollama_url=_env("CASCABEL_OLLAMA_URL", "http://localhost:11434/api/generate"),
        ollama_model=_env("CASCABEL_OLLAMA_MODEL", "mistral"),
        llm_timeout_s=_env_int("CASCABEL_LLM_TIMEOUT_S", 20),
        max_refine_iterations=_env_int("CASCABEL_MAX_REFINE", 3),
        api_host=_env("CASCABEL_API_HOST", "127.0.0.1"),
        api_port=_env_int("CASCABEL_API_PORT", 8888),
    )


CONFIG = load_config()
