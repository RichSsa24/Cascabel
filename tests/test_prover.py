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
        'logic': {
            'process_name': 'echo'
        }
    }
    
    fires = prove_detection(yaml.dump(rule), events)
    assert fires is True
    
    rule2 = {
        'logic': {
            'process_name': 'bash'
        }
    }
    
    fires = prove_detection(yaml.dump(rule2), events)
    assert fires is False
