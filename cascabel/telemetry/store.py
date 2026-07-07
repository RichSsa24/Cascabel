import sqlite3
from typing import List
from datetime import datetime
from .schema import NormalizedEvent

from cascabel.config import CONFIG

def init_db():
    conn = sqlite3.connect(CONFIG.db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            host TEXT,
            source TEXT,
            event_id TEXT,
            process_name TEXT,
            command_line TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_event(event: NormalizedEvent):
    init_db()
    conn = sqlite3.connect(CONFIG.db_path)
    c = conn.cursor()
    c.execute('''
        INSERT INTO events (timestamp, host, source, event_id, process_name, command_line)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        event.timestamp.isoformat(),
        event.host,
        event.source,
        event.event_id,
        event.process_name,
        event.command_line
    ))
    conn.commit()
    conn.close()

def get_events_for_host_in_window(host: str, start: datetime, end: datetime) -> List[NormalizedEvent]:
    init_db()
    conn = sqlite3.connect(CONFIG.db_path)
    c = conn.cursor()
    
    # SQLite datetime comparison works with ISO strings
    c.execute('''
        SELECT timestamp, host, source, event_id, process_name, command_line
        FROM events
        WHERE host = ? AND timestamp >= ? AND timestamp <= ?
    ''', (host, start.isoformat(), end.isoformat()))
    
    rows = c.fetchall()
    conn.close()
    
    events = []
    for row in rows:
        events.append(NormalizedEvent(
            timestamp=datetime.fromisoformat(row[0]),
            host=row[1],
            source=row[2],
            event_id=row[3],
            process_name=row[4],
            command_line=row[5]
        ))
    return events
