from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TestVariant:
    name: str
    description: str
    supported_platforms: List[str]
    command: str
    cleanup: Optional[str] = None

@dataclass
class AtomicTest:
    technique_id: str
    name: str
    tactic: str
    variants: List[TestVariant]

@dataclass
class RunResult:
    technique_id: str
    variant_name: str
    target: str
    status: str
    start_time: str
    end_time: str
    stdout: str
    stderr: str
    returncode: int
