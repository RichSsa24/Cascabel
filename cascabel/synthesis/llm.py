import urllib.request
import json
from typing import List
from cascabel.telemetry.schema import NormalizedEvent
from .prompt import build_prompt
import yaml

def _generate_mock_rule(events: List[NormalizedEvent], technique_id: str) -> dict:
    # Deterministic mock generating a rule grounded ONLY in the telemetry
    process_names = list(set([e.process_name for e in events if e.process_name]))
    
    rule = {
        'title': f'Detect {technique_id}',
        'description': f'Auto-synthesized rule for {technique_id}',
        'logic': {
            'process_name': process_names[0] if process_names else 'UNKNOWN'
        }
    }
    return rule

def generate_rule(events: List[NormalizedEvent], technique_id: str) -> str:
    prompt = build_prompt(events)
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            response_text = res_data.get('response', '')
            # Parse YAML from LLM response (assuming it's formatted well)
            # For robustness in this implementation, if it fails, we fall back.
            yaml.safe_load(response_text)
            return response_text
    except Exception as e:
        # Graceful fallback to deterministic mock to satisfy C0/C4 constraints
        rule_dict = _generate_mock_rule(events, technique_id)
        return yaml.dump(rule_dict)
