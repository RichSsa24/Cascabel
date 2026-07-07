import json
import hashlib
import os

from cascabel.config import CONFIG

def _hash_entry(entry_str: str) -> str:
    return hashlib.sha256(entry_str.encode('utf-8')).hexdigest()

def append_entry(action: str, details: dict):
    prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    if os.path.exists(CONFIG.ledger_path):
        with open(CONFIG.ledger_path, 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    prev_hash = _hash_entry(last_line)
                    
    entry = {
        'action': action,
        'details': details,
        'prev_hash': prev_hash
    }
    
    entry_str = json.dumps(entry, sort_keys=True)
    with open(CONFIG.ledger_path, 'a') as f:
        f.write(entry_str + '\n')

def verify_ledger() -> bool:
    if not os.path.exists(CONFIG.ledger_path):
        return True
        
    expected_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    with open(CONFIG.ledger_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            
            if entry.get('prev_hash') != expected_prev_hash:
                return False
                
            expected_prev_hash = _hash_entry(line)
            
    return True
