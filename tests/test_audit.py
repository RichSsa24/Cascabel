import pytest
import os
import json
import cascabel.audit.ledger as ledger

def test_ledger_append_and_verify(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(ledger, 'LEDGER_PATH', str(ledger_path))
    
    ledger.append_entry("START", {"target": "127.0.0.1"})
    ledger.append_entry("RUN", {"technique": "T1059.001"})
    
    assert ledger.verify_ledger() is True

def test_ledger_tampering(tmp_path, monkeypatch):
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(ledger, 'LEDGER_PATH', str(ledger_path))
    
    ledger.append_entry("START", {"target": "127.0.0.1"})
    ledger.append_entry("RUN", {"technique": "T1059.001"})
    ledger.append_entry("END", {"status": "success"})
    
    # Read and tamper
    with open(ledger_path, 'r') as f:
        lines = f.readlines()
        
    entry = json.loads(lines[1])
    entry['details']['technique'] = "T1059.003" # Tampered!
    lines[1] = json.dumps(entry) + "\n"
    
    with open(ledger_path, 'w') as f:
        f.writelines(lines)
        
    assert ledger.verify_ledger() is False
