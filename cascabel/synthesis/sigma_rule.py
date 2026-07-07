"""Sigma rule construction, parsing, and a minimal in-lab evaluator.

CASCABEL synthesizes real Sigma-format rules (status: candidate) grounded in
observed telemetry. pySigma is used to lint them for structural validity; a
small evaluator matches the subset of Sigma we emit against NormalizedEvents
so the loop can prove a rule fires without a full detection-engine backend.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml

from cascabel.telemetry.schema import NormalizedEvent

# Map Sigma field names -> NormalizedEvent attributes (single source of truth).
FIELD_MAP: Dict[str, str] = {
    "Image": "process_name",
    "ProcessName": "process_name",
    "CommandLine": "command_line",
    "Source": "source",
    "EventID": "event_id",
}

_SUPPORTED_MODIFIERS = {"", "contains", "startswith", "endswith"}


@dataclass
class Selector:
    field: str          # Sigma field name, e.g. "Image"
    modifier: str       # "", "contains", "startswith", "endswith"
    value: str
    attr: str           # resolved NormalizedEvent attribute

    def matches_value(self, observed: str) -> bool:
        if observed is None:
            return False
        if self.modifier == "contains":
            return self.value in observed
        if self.modifier == "startswith":
            return observed.startswith(self.value)
        if self.modifier == "endswith":
            return observed.endswith(self.value)
        return observed == self.value


class UngroundableTelemetryError(Exception):
    """No distinguishing telemetry field exists to build a grounded rule."""


def _stable_id(technique_id: str, process_name: str) -> str:
    digest = hashlib.sha256(f"{technique_id}:{process_name}".encode("utf-8")).hexdigest()
    return f"{digest[0:8]}-{digest[8:12]}-{digest[12:16]}-{digest[16:20]}-{digest[20:32]}"


def build_grounded_rule(
    events: List[NormalizedEvent], technique_id: str, tactic: str = ""
) -> str:
    """Deterministically build a Sigma rule grounded ONLY in observed events.

    Used as the safe local synthesis path and as the fallback when the runtime
    LLM is unavailable or emits an ungrounded rule.
    """
    process_names = [e.process_name for e in events if e.process_name]
    if not process_names:
        raise UngroundableTelemetryError(
            "No process_name telemetry available to ground a rule"
        )

    # Prefer the least common process name in the window as the anchor: it is
    # the most distinguishing signal for the emulated technique.
    anchor = min(set(process_names), key=process_names.count)

    detection: Dict[str, object] = {"selection": {"Image|endswith": anchor}}

    # Add a distinctive command-line substring when telemetry provides one.
    cmd = next(
        (e.command_line for e in events if e.process_name == anchor and e.command_line),
        "",
    )
    token = _distinctive_token(cmd)
    if token:
        detection["selection"]["CommandLine|contains"] = token

    detection["condition"] = "selection"

    rule = {
        "title": f"Emulated {technique_id} via {anchor}",
        "id": _stable_id(technique_id, anchor),
        "status": "candidate",
        "description": (
            f"Lab-synthesized detection for ATT&CK {technique_id}, grounded in "
            f"telemetry observed during CASCABEL emulation."
        ),
        "references": [f"https://attack.mitre.org/techniques/{technique_id.replace('.', '/')}/"],
        "author": "CASCABEL (AI candidate, human review required)",
        "tags": [f"attack.{technique_id.lower()}"] + ([f"attack.{tactic.lower().replace(' ', '_')}"] if tactic else []),
        "logsource": {"product": "linux", "category": "process_creation"},
        "detection": detection,
        "falsepositives": ["Legitimate administrative use of the same binary"],
        "level": "medium",
    }
    return yaml.dump(rule, sort_keys=False)


def _distinctive_token(command_line: str) -> Optional[str]:
    """Pick a distinctive, telemetry-present token from a command line."""
    if not command_line:
        return None
    # Favor tokens that look like emulation markers or account/file names.
    for tok in command_line.replace("'", " ").replace('"', " ").split():
        if tok.startswith("cascabel") or tok.startswith("/tmp/"):
            return tok
    return None


def parse_selectors(rule_yaml: str) -> List[Selector]:
    """Extract all field selectors from a Sigma rule's detection block."""
    rule = yaml.safe_load(rule_yaml)
    if not isinstance(rule, dict):
        raise ValueError("Rule is not a valid mapping")

    detection = rule.get("detection", {})
    if not isinstance(detection, dict):
        raise ValueError("Rule has no valid detection block")

    selectors: List[Selector] = []
    for name, block in detection.items():
        if name == "condition" or not isinstance(block, dict):
            continue
        for raw_key, raw_value in block.items():
            field_name, _, modifier = raw_key.partition("|")
            if modifier not in _SUPPORTED_MODIFIERS:
                raise ValueError(f"Unsupported Sigma modifier: {modifier}")
            attr = FIELD_MAP.get(field_name)
            if attr is None:
                raise ValueError(f"Unknown Sigma field '{field_name}' (not in FIELD_MAP)")
            values = raw_value if isinstance(raw_value, list) else [raw_value]
            for value in values:
                selectors.append(
                    Selector(field=field_name, modifier=modifier, value=str(value), attr=attr)
                )
    return selectors


def _named_selections(rule: dict) -> Dict[str, List[Selector]]:
    detection = rule.get("detection", {})
    result: Dict[str, List[Selector]] = {}
    for name, block in detection.items():
        if name == "condition" or not isinstance(block, dict):
            continue
        selectors: List[Selector] = []
        for raw_key, raw_value in block.items():
            field_name, _, modifier = raw_key.partition("|")
            attr = FIELD_MAP.get(field_name)
            if attr is None:
                continue
            values = raw_value if isinstance(raw_value, list) else [raw_value]
            for value in values:
                selectors.append(
                    Selector(field=field_name, modifier=modifier, value=str(value), attr=attr)
                )
        result[name] = selectors
    return result


def _event_matches_selection(selectors: List[Selector], event: NormalizedEvent) -> bool:
    return all(sel.matches_value(getattr(event, sel.attr, None)) for sel in selectors)


def evaluate_rule(rule_yaml: str, events: List[NormalizedEvent]) -> bool:
    """Return True if the Sigma rule fires on at least one event.

    Supports the condition forms CASCABEL emits: a single selection name,
    'A and B', 'A or B', '1 of them', 'all of them'.
    """
    rule = yaml.safe_load(rule_yaml)
    if not isinstance(rule, dict):
        return False

    selections = _named_selections(rule)
    if not selections:
        return False

    condition = str(rule.get("detection", {}).get("condition", "")).strip()

    for event in events:
        per_selection = {
            name: _event_matches_selection(sels, event) for name, sels in selections.items()
        }
        if _condition_holds(condition, per_selection):
            return True
    return False


def _condition_holds(condition: str, per_selection: Dict[str, bool]) -> bool:
    if not condition:
        return False
    lowered = condition.lower()
    if lowered == "all of them":
        return all(per_selection.values())
    if lowered in ("1 of them", "any of them"):
        return any(per_selection.values())
    if " and " in lowered:
        return all(per_selection.get(part.strip(), False) for part in lowered.split(" and "))
    if " or " in lowered:
        return any(per_selection.get(part.strip(), False) for part in lowered.split(" or "))
    return per_selection.get(condition.strip(), False)
