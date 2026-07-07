import json
from datetime import datetime, timezone
from typing import List
from .schema import NormalizedEvent

def parse_mock_audit_log(filepath: str) -> List[NormalizedEvent]:
    events = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                timestamp_str = data.get('timestamp')
                timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now(timezone.utc)
                
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                    
                event = NormalizedEvent(
                    timestamp=timestamp,
                    host=data.get('host', 'unknown'),
                    source=data.get('source', 'mock_auditd'),
                    event_id=data.get('event_id', 'SYSCALL'),
                    process_name=data.get('process_name', ''),
                    command_line=data.get('command_line', '')
                )
                events.append(event)
            except Exception as e:
                print(f"Failed to parse log line: {e}")
    return events
