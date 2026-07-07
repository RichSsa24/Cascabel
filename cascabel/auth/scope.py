from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timezone
import yaml
from .crypto import verify_signature

@dataclass
class ScopeContract:
    allowed_targets: List[str]
    allowed_techniques: List[str]
    valid_from: datetime
    valid_until: datetime
    max_hosts: int = 1
    max_actions_per_run: int = 10
    dry_run: bool = True

class Scope:
    def __init__(self, contract: ScopeContract, signature: str):
        self.contract = contract
        self.signature = signature
        
    @classmethod
    def load(cls, scope_yaml_path: str, public_key_pem_path: str) -> 'Scope':
        with open(scope_yaml_path, 'r') as f:
            raw_content = f.read()
            
        parts = raw_content.split('---')
        if len(parts) < 2:
            raise ValueError("Invalid scope.yaml format. Expected document and signature separated by ---")
            
        contract_yaml = parts[0].strip()
        signature_part = parts[1].strip()
        
        sig_data = yaml.safe_load(signature_part)
        signature = sig_data.get('signature') if sig_data else None
        
        if not signature:
            raise ValueError("No signature found in scope.yaml")
            
        with open(public_key_pem_path, 'rb') as f:
            public_key_pem = f.read()
            
        if not verify_signature(public_key_pem, contract_yaml.encode('utf-8'), signature):
            raise ValueError("Invalid signature on scope contract")
            
        data = yaml.safe_load(contract_yaml)
        
        # Parse dates
        valid_from_str = data.get('valid_from')
        valid_until_str = data.get('valid_until')
        
        # very simple ISO parsing fallback
        if isinstance(valid_from_str, str):
            valid_from = datetime.fromisoformat(valid_from_str.replace('Z', '+00:00'))
        else:
            valid_from = valid_from_str
            
        if isinstance(valid_until_str, str):
            valid_until = datetime.fromisoformat(valid_until_str.replace('Z', '+00:00'))
        else:
            valid_until = valid_until_str
            
        # Add timezone to naive datetime if missing
        if valid_from.tzinfo is None:
            valid_from = valid_from.replace(tzinfo=timezone.utc)
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
            
        contract = ScopeContract(
            allowed_targets=data.get('allowed_targets', []),
            allowed_techniques=data.get('allowed_techniques', []),
            valid_from=valid_from,
            valid_until=valid_until,
            max_hosts=data.get('max_hosts', 1),
            max_actions_per_run=data.get('max_actions_per_run', 10),
            dry_run=data.get('dry_run', True)
        )
        
        now = datetime.now(timezone.utc)
        if now < contract.valid_from or now > contract.valid_until:
            raise ValueError(f"Scope is not currently valid. Valid from {contract.valid_from} to {contract.valid_until}")
            
        return cls(contract, signature)
