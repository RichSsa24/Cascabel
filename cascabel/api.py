import os
import json
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from cascabel.config import CONFIG
from cascabel.optimizer.greedy import get_covered_techniques
from cascabel.orchestrator.engine import load_tests

app = FastAPI(title="CASCABEL API")

# Add CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/ledger")
def get_ledger():
    if not os.path.exists(CONFIG.ledger_path):
        return []
    entries = []
    with open(CONFIG.ledger_path, "r") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    # Return reversed so newest is first
    return list(reversed(entries))

@app.get("/api/detections")
def get_detections():
    if not os.path.exists(CONFIG.detections_dir):
        return []
    
    rules = []
    for f in os.listdir(CONFIG.detections_dir):
        if f.endswith(".yaml"):
            with open(os.path.join(CONFIG.detections_dir, f), "r") as rule_f:
                try:
                    rule = yaml.safe_load(rule_f)
                    rules.append(rule)
                except Exception:
                    pass
    return rules

@app.get("/api/coverage")
def get_coverage():
    tests = load_tests(CONFIG.atomics_dir)
    covered_techs = get_covered_techniques()
    
    total = len(tests)
    covered = len([t for t in tests if t.technique_id in covered_techs])
    
    tactic_coverage = {}
    for test in tests:
        is_covered = test.technique_id in covered_techs
        for tactic in test.tactics:
            if tactic not in tactic_coverage:
                tactic_coverage[tactic] = {"total": 0, "covered": 0}
            tactic_coverage[tactic]["total"] += 1
            if is_covered:
                tactic_coverage[tactic]["covered"] += 1
                
    return {
        "total_techniques": total,
        "covered_techniques": covered,
        "tactics": tactic_coverage
    }

# Serve static frontend if it exists
frontend_build = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_build):
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")
