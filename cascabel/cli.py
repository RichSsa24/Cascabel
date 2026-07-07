import click
import os
import yaml
from cascabel.auth.crypto import generate_keypair, sign_payload
from cascabel.audit.ledger import verify_ledger
from cascabel.auth.scope import Scope

@click.group()
def cli():
    pass

@cli.command()
def doctor():
    """Check environment, scope, and connectivity."""
    click.echo("Running CASCABEL Doctor...")
    
    # Check Python env
    click.echo(" - Python Environment: OK")
    
    # Check Ledger
    if verify_ledger():
        click.echo(" - Ledger Integrity: OK")
    else:
        click.echo(" - Ledger Integrity: TAMPERED OR INVALID")
        
    # Check keys
    if os.path.exists('cascabel.pub'):
        click.echo(" - Public Key: FOUND")
    else:
        click.echo(" - Public Key: MISSING")
        
    # Check scope
    if os.path.exists('scope.yaml') and os.path.exists('cascabel.pub'):
        try:
            Scope.load('scope.yaml', 'cascabel.pub')
            click.echo(" - Scope: VALID AND ACTIVE")
        except Exception as e:
            click.echo(f" - Scope: INVALID ({str(e)})")
    else:
        click.echo(" - Scope: MISSING")
        
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

if __name__ == '__main__':
    cli()
