import click
import os
import yaml
from cascabel.auth.crypto import generate_keypair, sign_payload
from cascabel.audit.ledger import verify_ledger, append_entry
from cascabel.auth.scope import Scope
from cascabel.orchestrator.engine import load_tests, filter_by_scope, execute_test, execute_cleanup
from cascabel.telemetry.store import init_db, insert_event
from cascabel.telemetry.normalizer import parse_mock_audit_log
from cascabel.telemetry.correlator import correlate_emulation, find_last_emulation_in_ledger, InsufficientTelemetryError
from cascabel.synthesis.llm import generate_rule
from cascabel.synthesis.prover import prove_detection

@click.group()
def cli():
    pass

@cli.command()
def doctor():
    """Check environment, scope, and connectivity."""
    click.echo("Running CASCABEL Doctor...")
    
    click.echo(" - Python Environment: OK")
    
    if verify_ledger():
        click.echo(" - Ledger Integrity: OK")
    else:
        click.echo(" - Ledger Integrity: TAMPERED OR INVALID")
        
    if os.path.exists('cascabel.pub'):
        click.echo(" - Public Key: FOUND")
    else:
        click.echo(" - Public Key: MISSING")
        
    scope = None
    if os.path.exists('scope.yaml') and os.path.exists('cascabel.pub'):
        try:
            scope = Scope.load('scope.yaml', 'cascabel.pub')
            click.echo(" - Scope: VALID AND ACTIVE")
        except Exception as e:
            click.echo(f" - Scope: INVALID ({str(e)})")
    else:
        click.echo(" - Scope: MISSING")

    # Connectivity Smoke Test
    if scope and scope.contract.allowed_targets:
        import urllib.request
        target = scope.contract.allowed_targets[0]
        try:
            req = urllib.request.Request(f"http://{target}:8080/run", method='OPTIONS')
            with urllib.request.urlopen(req, timeout=2) as response:
                pass
            click.echo(f" - Connectivity to {target}: OK")
        except Exception as e:
            if hasattr(e, 'code'):
                click.echo(f" - Connectivity to {target}: OK")
            else:
                click.echo(f" - Connectivity to {target}: FAILED ({e})")
        
    click.echo("Doctor check complete.")

@cli.command()
def generate_keys():
    """Generate Ed25519 keypair for scope signing."""
    priv, pub = generate_keypair()
    with open('cascabel.key', 'wb') as f:
        f.write(priv)
    with open('cascabel.pub', 'wb') as f:
        f.write(pub)
    click.echo("Keys generated: cascabel.key, cascabel.pub")

@cli.command()
@click.argument('scope_file')
@click.argument('key_file')
def sign_scope(scope_file, key_file):
    """Sign a scope.yaml file using the provided private key."""
    with open(scope_file, 'r') as f:
        content = f.read().split('---')[0].strip()
        
    with open(key_file, 'rb') as f:
        private_key_pem = f.read()
        
    signature = sign_payload(private_key_pem, content.encode('utf-8'))
    
    signed_content = f"{content}\n---\nsignature: {signature}\n"
    
    with open(scope_file, 'w') as f:
        f.write(signed_content)
        
    click.echo(f"Scope {scope_file} signed successfully.")

@cli.command()
@click.argument('technique_id')
def run(technique_id):
    """Run an emulation for the given technique ID."""
    try:
        scope = Scope.load('scope.yaml', 'cascabel.pub')
    except Exception as e:
        click.echo(f"Scope validation failed: {e}")
        return
        
    tests = load_tests('data/atomics')
    allowed_tests = filter_by_scope(tests, scope)
    
    target_test = None
    for t in allowed_tests:
        if t.technique_id == technique_id:
            target_test = t
            break
            
    if not target_test:
        click.echo(f"Technique {technique_id} is either not in scope or has no implementation.")
        for t in tests:
            if t.technique_id == technique_id:
                append_entry("BLOCKED", {"technique": technique_id, "reason": "out_of_scope"})
                return
        return
        
    target_ip = scope.contract.allowed_targets[0]
    
    if scope.contract.dry_run:
        click.echo(f"[DRY RUN] Would execute {technique_id} on {target_ip}")
        return
        
    append_entry("EMULATION_START", {"technique": technique_id, "target": target_ip})
    click.echo(f"Executing {technique_id} on {target_ip}...")
    
    res = execute_test(target_test, 0, target_ip)
    
    append_entry("EMULATION_END", {
        "technique": technique_id,
        "target": target_ip,
        "status": res.status,
        "returncode": res.returncode,
        "start_time": res.start_time,
        "end_time": res.end_time
    })
    
    click.echo(f"Result: {res.status}, returncode: {res.returncode}")
    if res.stdout:
        click.echo(f"STDOUT:\n{res.stdout}")
        
    click.echo(f"Running cleanup for {technique_id}...")
    cleanup_success = execute_cleanup(target_test, 0, target_ip)
    
    append_entry("CLEANUP_END", {
        "technique": technique_id,
        "target": target_ip,
        "success": cleanup_success
    })
    
    click.echo(f"Cleanup success: {cleanup_success}")

@cli.command()
@click.argument('logfile')
def ingest(logfile):
    """Ingest and normalize telemetry logs."""
    init_db()
    events = parse_mock_audit_log(logfile)
    for event in events:
        insert_event(event)
    click.echo(f"Ingested {len(events)} events from {logfile}.")

@cli.command()
@click.argument('technique_id')
def correlate(technique_id):
    """Correlate telemetry for the last run of a technique."""
    try:
        run_data = find_last_emulation_in_ledger(technique_id)
        click.echo(f"Found run for {technique_id} on {run_data['target']} from {run_data['start_time']} to {run_data['end_time']}")
        
        tech, events = correlate_emulation(technique_id, run_data['target'], run_data['start_time'], run_data['end_time'])
        click.echo(f"Correlated {len(events)} events:")
        for e in events:
            click.echo(f"  [{e.timestamp}] {e.source} {e.event_id} - {e.process_name}: {e.command_line}")
            
    except InsufficientTelemetryError as e:
        click.echo(str(e))
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.argument('technique_id')
def synthesize(technique_id):
    """Synthesize a detection rule from telemetry."""
    try:
        run_data = find_last_emulation_in_ledger(technique_id)
        tech, events = correlate_emulation(technique_id, run_data['target'], run_data['start_time'], run_data['end_time'])
        
        click.echo(f"Synthesizing rule for {technique_id} based on {len(events)} events...")
        rule_yaml = generate_rule(events, technique_id)
        
        out_path = f"data/detections/{technique_id}.yaml"
        with open(out_path, 'w') as f:
            f.write(rule_yaml)
            
        click.echo(f"Rule written to {out_path}")
        
    except Exception as e:
        click.echo(f"Synthesis Error: {str(e)}")

@cli.command()
@click.argument('technique_id')
def prove(technique_id):
    """Prove a detection rule against telemetry."""
    try:
        rule_path = f"data/detections/{technique_id}.yaml"
        if not os.path.exists(rule_path):
            click.echo(f"Rule file {rule_path} not found.")
            return
            
        with open(rule_path, 'r') as f:
            rule_yaml = f.read()
            
        run_data = find_last_emulation_in_ledger(technique_id)
        tech, events = correlate_emulation(technique_id, run_data['target'], run_data['start_time'], run_data['end_time'])
        
        fires = prove_detection(rule_yaml, events)
        if fires:
            click.echo(f"PROVE_SUCCESS: Rule {technique_id} successfully fired on the correlated telemetry!")
            append_entry("PROVE_SUCCESS", {"technique": technique_id, "target": run_data['target']})
        else:
            click.echo(f"PROVE_FAILED: Rule {technique_id} did not fire on the correlated telemetry.")
            append_entry("PROVE_FAILED", {"technique": technique_id, "target": run_data['target']})
            
    except Exception as e:
        click.echo(f"Prove Error: {str(e)}")

if __name__ == '__main__':
    cli()
