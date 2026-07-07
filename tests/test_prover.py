import pytest
from datetime import datetime, timezone
from cascabel.telemetry.schema import NormalizedEvent
from cascabel.synthesis.prover import prove_detection
import yaml

def test_prover():
    events = [
        NormalizedEvent(
            timestamp=datetime.now(timezone.utc),
            host="127.0.0.1",
            source="mock",
            event_id="EXECVE",
            process_name="echo",
            command_line="echo hello"
        )
    ]
    
    rule = {
        'detection': {
            'selection': {
                'Image|endswith': 'echo'
            },
            'condition': 'selection'
        }
    }
    
    fires = prove_detection(yaml.dump(rule), events)
    assert fires is True
    
    rule2 = {
        'detection': {
            'selection': {
                'Image|endswith': 'bash'
            },
            'condition': 'selection'
        }
    }
    
    fires = prove_detection(yaml.dump(rule2), events)
    assert fires is False
