import os
from typing import List, Dict, Tuple
from cascabel.orchestrator.engine import AtomicTest
from cascabel.config import CONFIG

def get_covered_techniques() -> List[str]:
    """Returns a list of technique IDs that already have a detection rule."""
    if not os.path.exists(CONFIG.detections_dir):
        return []
    
    covered = []
    for f in os.listdir(CONFIG.detections_dir):
        if f.endswith(".yaml"):
            covered.append(f.replace(".yaml", ""))
    return covered

def optimize_coverage(available_tests: List[AtomicTest]) -> List[Tuple[float, AtomicTest]]:
    """
    Submodular greedy optimizer for ATT&CK coverage.
    Scores tests based on marginal coverage gain (prioritizing tactics with 0 coverage).
    Returns a sorted list of (score, AtomicTest).
    """
    covered_techs = get_covered_techniques()
    
    # Calculate current tactic coverage
    covered_tactics: Dict[str, int] = {}
    for test in available_tests:
        if test.technique_id in covered_techs:
            for tactic in [test.tactic]:
                covered_tactics[tactic] = covered_tactics.get(tactic, 0) + 1
                
    backlog = [t for t in available_tests if t.technique_id not in covered_techs]
    
    scored_tests = []
    for test in backlog:
        score = 0.0
        # Marginal gain: +1.0 for the technique itself
        score += 1.0 
        
        # Marginal tactic gain: +0.5 for each tactic not yet covered
        for tactic in [test.tactic]:
            if covered_tactics.get(tactic, 0) == 0:
                score += 0.5
            else:
                score += 0.1 / covered_tactics[tactic]
                
        scored_tests.append((score, test))
        
    # Sort descending by score
    scored_tests.sort(key=lambda x: x[0], reverse=True)
    return scored_tests
