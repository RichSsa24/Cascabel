import pytest
from datetime import datetime, timezone
from cascabel.telemetry.schema import NormalizedEvent
from cascabel.synthesis.prompt import build_prompt
from cascabel.synthesis.llm import generate_rule, UngroundedRuleError
from cascabel.synthesis.providers import MockProvider

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
    
def test_mock_provider_synthesis():
    event = NormalizedEvent(
        timestamp=datetime.now(timezone.utc),
        host="127.0.0.1",
        source="mock",
        event_id="EXECVE",
        process_name="cat",
        command_line="cat /etc/passwd"
    )
    # Valid YAML grounded in "cat"
    valid_yaml = '''
title: Detect T1003
status: candidate
detection:
  selection:
    Image|endswith: cat
  condition: selection
'''
    provider = MockProvider(response=valid_yaml)
    rule_yaml = generate_rule([event], "T1003", provider=provider)
    assert 'Image|endswith: cat' in rule_yaml
    assert 'attack.t1003' in rule_yaml

def test_ungrounded_fallback():
    event = NormalizedEvent(
        timestamp=datetime.now(timezone.utc),
        host="127.0.0.1",
        source="mock",
        event_id="EXECVE",
        process_name="cat",
        command_line="cat /etc/passwd"
    )
    # Hallucination
    invalid_yaml = '''
title: Detect T1003
detection:
  selection:
    Image|endswith: mimikatz
  condition: selection
'''
    provider = MockProvider(response=invalid_yaml)
    rule_yaml = generate_rule([event], "T1003", provider=provider)
    # It should fallback to deterministic rule which uses 'cat'
    assert 'Image|endswith: cat' in rule_yaml
    assert 'mimikatz' not in rule_yaml
