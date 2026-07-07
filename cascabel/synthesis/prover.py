import yaml
from typing import List
from cascabel.telemetry.schema import NormalizedEvent

def prove_detection(rule_yaml: str, events: List[NormalizedEvent]) -> bool:
    """
    Evaluates the simple YAML rule against the list of events.
    Returns True if the rule fires on AT LEAST ONE event.
    """
    try:
        rule = yaml.safe_load(rule_yaml)
    except Exception:
        return False
        
    logic = rule.get('logic', {})
    expected_process = logic.get('process_name')
    
    if not expected_process:
        return False
        
    for event in events:
        if event.process_name == expected_process:
            return True
            
    return False
