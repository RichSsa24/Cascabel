from typing import List
from cascabel.telemetry.schema import NormalizedEvent
from cascabel.synthesis.sigma_rule import evaluate_rule

def prove_detection(rule_yaml: str, events: List[NormalizedEvent]) -> bool:
    """
    Evaluates a Sigma YAML rule against the list of events.
    Returns True if the rule fires on AT LEAST ONE event.
    """
    try:
        return evaluate_rule(rule_yaml, events)
    except Exception:
        return False
