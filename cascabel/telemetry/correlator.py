from datetime import datetime, timedelta, timezone
from typing import List, Tuple
import json
from .schema import NormalizedEvent
from .store import get_events_for_host_in_window

class InsufficientTelemetryError(Exception):
    pass

def correlate_emulation(technique_id: str, target: str, start_time: datetime, end_time: datetime) -> Tuple[str, List[NormalizedEvent]]:
    """
    Correlates telemetry events to an emulation run.
    Uses a time window: [start_time - 1s, end_time + 2s]
    """
    window_start = start_time - timedelta(seconds=1)
    window_end = end_time + timedelta(seconds=2)
    
    events = get_events_for_host_in_window(target, window_start, window_end)
    
    if not events:
        raise InsufficientTelemetryError(f"INSUFFICIENT_TELEMETRY: No events found for host {target} between {window_start.isoformat()} and {window_end.isoformat()}")
        
    return technique_id, events

def find_last_emulation_in_ledger(technique_id: str) -> dict:
    with open('ledger.jsonl', 'r') as f:
        lines = f.readlines()
        
    for line in reversed(lines):
        entry = json.loads(line.strip())
        action = entry.get('action')
        details = entry.get('details', {})
        
        if action == 'EMULATION_END' and details.get('technique') == technique_id:
            st_str = details.get('start_time')
            et_str = details.get('end_time')
            if not st_str or not et_str:
                continue
                
            start_time = datetime.fromisoformat(st_str)
            end_time = datetime.fromisoformat(et_str)
            
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
                
            return {
                'target': details.get('target'),
                'start_time': start_time,
                'end_time': end_time
            }
            
    raise ValueError(f"Could not find valid EMULATION_END with timestamps for {technique_id} in ledger.")
