import pytest
from datetime import datetime, timezone, timedelta
from cascabel.telemetry.schema import NormalizedEvent
from cascabel.telemetry.normalizer import parse_mock_audit_log
from cascabel.telemetry.correlator import correlate_emulation, InsufficientTelemetryError
import cascabel.telemetry.store as store

def test_normalizer(tmp_path):
    log_file = tmp_path / "mock_audit.log"
    log_content = '{"timestamp": "2024-01-01T12:00:00+00:00", "host": "127.0.0.1", "source": "mock_auditd", "event_id": "EXECVE", "process_name": "echo", "command_line": "echo hello"}\n'
    log_file.write_text(log_content)
    
    events = parse_mock_audit_log(str(log_file))
    assert len(events) == 1
    assert events[0].process_name == "echo"
    assert events[0].command_line == "echo hello"

def test_correlator(tmp_path, monkeypatch):
    db_path = tmp_path / "test_telemetry.db"
    monkeypatch.setattr(store, 'DB_PATH', str(db_path))
    
    store.init_db()
    
    now = datetime.now(timezone.utc)
    
    # Insert event inside window
    store.insert_event(NormalizedEvent(
        timestamp=now,
        host="127.0.0.1",
        source="mock_auditd",
        event_id="EXECVE",
        process_name="echo",
        command_line="echo test"
    ))
    
    # Insert event outside window
    store.insert_event(NormalizedEvent(
        timestamp=now - timedelta(minutes=5),
        host="127.0.0.1",
        source="mock_auditd",
        event_id="EXECVE",
        process_name="ping",
        command_line="ping 8.8.8.8"
    ))
    
    tech, events = correlate_emulation("T1059.004", "127.0.0.1", now - timedelta(seconds=10), now + timedelta(seconds=10))
    
    assert len(events) == 1
    assert events[0].process_name == "echo"
    
def test_correlator_insufficient(tmp_path, monkeypatch):
    db_path = tmp_path / "test_telemetry.db"
    monkeypatch.setattr(store, 'DB_PATH', str(db_path))
    
    store.init_db()
    
    now = datetime.now(timezone.utc)
    with pytest.raises(InsufficientTelemetryError, match="INSUFFICIENT_TELEMETRY"):
        correlate_emulation("T1059.004", "127.0.0.1", now - timedelta(seconds=10), now + timedelta(seconds=10))
