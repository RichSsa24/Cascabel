from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class NormalizedEvent:
    timestamp: datetime
    host: str
    source: str
    event_id: str
    process_name: str
    command_line: str
