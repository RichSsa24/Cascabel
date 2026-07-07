import pytest
from datetime import datetime, timezone
from cascabel.telemetry.schema import NormalizedEvent
from cascabel.synthesis.prompt import build_prompt
from cascabel.synthesis.llm import _generate_mock_rule

def test_prompt_builder():
    event = NormalizedEvent(
        timestamp=datetime.now(timezone.utc),
        host="127.0.0.1",
        source="mock_auditd",
        event_id="EXECVE",
        process_name="echo",
        command_line="echo hello"
    )
    prompt = build_prompt([event])
    assert "echo" in prompt
    assert "echo hello" in prompt
    
def test_mock_rule_generation():
    event = NormalizedEvent(
        timestamp=datetime.now(timezone.utc),
        host="127.0.0.1",
        source="mock",
        event_id="EXECVE",
        process_name="cat",
        command_line="cat /etc/passwd"
    )
    rule = _generate_mock_rule([event], "T1003")
    assert rule['logic']['process_name'] == "cat"
    assert rule['title'] == "Detect T1003"
