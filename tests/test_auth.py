import pytest
import os
import yaml
from datetime import datetime, timedelta, timezone
from cascabel.auth.crypto import generate_keypair, sign_payload, verify_signature
from cascabel.auth.scope import Scope, ScopeContract

def test_crypto_signing():
    priv, pub = generate_keypair()
    payload = b"test payload"
    sig = sign_payload(priv, payload)
    
    assert verify_signature(pub, payload, sig) is True
    assert verify_signature(pub, b"tampered payload", sig) is False

def test_scope_validation(tmp_path):
    priv, pub = generate_keypair()
    pub_path = tmp_path / "cascabel.pub"
    pub_path.write_bytes(pub)
    
    now = datetime.now(timezone.utc)
    valid_from = now - timedelta(days=1)
    valid_until = now + timedelta(days=1)
    
    scope_dict = {
        "allowed_targets": ["127.0.0.1"],
        "allowed_techniques": ["T1059.001"],
        "max_hosts": 1,
        "max_actions_per_run": 5,
        "valid_from": valid_from.isoformat(),
        "valid_until": valid_until.isoformat(),
        "dry_run": True
    }
    
    scope_yaml = yaml.dump(scope_dict).strip()
    sig = sign_payload(priv, scope_yaml.encode('utf-8'))
    signed_content = f"{scope_yaml}\n---\nsignature: {sig}\n"
    
    scope_path = tmp_path / "scope.yaml"
    scope_path.write_text(signed_content)
    
    scope = Scope.load(str(scope_path), str(pub_path))
    assert scope.contract.allowed_targets == ["127.0.0.1"]
    
def test_scope_expired(tmp_path):
    priv, pub = generate_keypair()
    pub_path = tmp_path / "cascabel.pub"
    pub_path.write_bytes(pub)
    
    now = datetime.now(timezone.utc)
    valid_from = now - timedelta(days=5)
    valid_until = now - timedelta(days=1)
    
    scope_dict = {
        "allowed_targets": ["127.0.0.1"],
        "allowed_techniques": ["T1059.001"],
        "valid_from": valid_from.isoformat(),
        "valid_until": valid_until.isoformat(),
    }
    
    scope_yaml = yaml.dump(scope_dict).strip()
    sig = sign_payload(priv, scope_yaml.encode('utf-8'))
    signed_content = f"{scope_yaml}\n---\nsignature: {sig}\n"
    
    scope_path = tmp_path / "scope.yaml"
    scope_path.write_text(signed_content)
    
    with pytest.raises(ValueError, match="Scope is not currently valid"):
        Scope.load(str(scope_path), str(pub_path))

def test_scope_invalid_signature(tmp_path):
    priv, pub = generate_keypair()
    priv2, pub2 = generate_keypair()
    
    pub_path = tmp_path / "cascabel.pub"
    pub_path.write_bytes(pub) # Save first pub key
    
    now = datetime.now(timezone.utc)
    scope_dict = {
        "allowed_targets": ["127.0.0.1"],
        "allowed_techniques": ["T1059.001"],
        "valid_from": (now - timedelta(days=1)).isoformat(),
        "valid_until": (now + timedelta(days=1)).isoformat(),
    }
    
    scope_yaml = yaml.dump(scope_dict).strip()
    # Sign with second private key
    sig = sign_payload(priv2, scope_yaml.encode('utf-8'))
    signed_content = f"{scope_yaml}\n---\nsignature: {sig}\n"
    
    scope_path = tmp_path / "scope.yaml"
    scope_path.write_text(signed_content)
    
    with pytest.raises(ValueError, match="Invalid signature"):
        Scope.load(str(scope_path), str(pub_path))
