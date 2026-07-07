import pytest
from cascabel.orchestrator.engine import load_tests, filter_by_scope
from cascabel.orchestrator.models import AtomicTest, TestVariant
from cascabel.auth.scope import Scope, ScopeContract
from datetime import datetime, timedelta, timezone

def test_filter_by_scope():
    tests = [
        AtomicTest(technique_id="T1059.004", name="A", tactic="T", variants=[]),
        AtomicTest(technique_id="T1082", name="B", tactic="T", variants=[]),
        AtomicTest(technique_id="T9999", name="C", tactic="T", variants=[])
    ]
    
    contract = ScopeContract(
        allowed_targets=["127.0.0.1"],
        allowed_techniques=["T1059.004", "T1082"],
        valid_from=datetime.now(timezone.utc) - timedelta(days=1),
        valid_until=datetime.now(timezone.utc) + timedelta(days=1)
    )
    
    scope = Scope(contract, "dummy_sig")
    
    filtered = filter_by_scope(tests, scope)
    assert len(filtered) == 2
    assert "T9999" not in [t.technique_id for t in filtered]
