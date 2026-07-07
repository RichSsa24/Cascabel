import yaml
import os
import urllib.request
import json
from typing import List
from .models import AtomicTest, TestVariant, RunResult
from cascabel.auth.scope import Scope

def load_tests(tests_dir: str) -> List[AtomicTest]:
    tests = []
    if not os.path.exists(tests_dir):
        return tests
        
    for filename in os.listdir(tests_dir):
        if not filename.endswith('.yaml'):
            continue
            
        filepath = os.path.join(tests_dir, filename)
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            
        variants = []
        for v_data in data.get('variants', []):
            variants.append(TestVariant(
                name=v_data.get('name'),
                description=v_data.get('description', ''),
                supported_platforms=v_data.get('supported_platforms', []),
                command=v_data.get('command'),
                cleanup=v_data.get('cleanup')
            ))
            
        test = AtomicTest(
            technique_id=data.get('technique_id'),
            name=data.get('name', ''),
            tactic=data.get('tactic', ''),
            variants=variants
        )
        tests.append(test)
    return tests

def filter_by_scope(tests: List[AtomicTest], scope: Scope) -> List[AtomicTest]:
    allowed = set(scope.contract.allowed_techniques)
    return [t for t in tests if t.technique_id in allowed]

def _send_command(target_ip: str, port: int, command: str) -> dict:
    url = f"http://{target_ip}:{port}/run"
    data = json.dumps({'command': command}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = response.read()
            return json.loads(res_data.decode('utf-8'))
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'start_time': '',
            'end_time': '',
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def execute_test(test: AtomicTest, variant_index: int, target_ip: str) -> RunResult:
    variant = test.variants[variant_index]
    res = _send_command(target_ip, 8080, variant.command)
    
    return RunResult(
        technique_id=test.technique_id,
        variant_name=variant.name,
        target=target_ip,
        status=res.get('status', 'error'),
        start_time=res.get('start_time', ''),
        end_time=res.get('end_time', ''),
        stdout=res.get('stdout', ''),
        stderr=res.get('stderr', ''),
        returncode=res.get('returncode', -1)
    )

def execute_cleanup(test: AtomicTest, variant_index: int, target_ip: str) -> bool:
    variant = test.variants[variant_index]
    if not variant.cleanup or variant.cleanup == 'echo "No cleanup needed"':
        return True
        
    res = _send_command(target_ip, 8080, variant.cleanup)
    return res.get('returncode') == 0
