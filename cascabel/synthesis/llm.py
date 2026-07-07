import yaml
from typing import List
from cascabel.telemetry.schema import NormalizedEvent
from cascabel.synthesis.prompt import build_prompt
from cascabel.synthesis.providers import get_provider, LLMProvider, LLMUnavailableError
from cascabel.synthesis.sigma_rule import (
    build_grounded_rule, 
    parse_selectors, 
    UngroundableTelemetryError
)

class UngroundedRuleError(Exception):
    """Raised when an LLM synthesizes a rule referencing unobserved telemetry."""

def validate_grounding(rule_yaml: str, events: List[NormalizedEvent]) -> None:
    """Ensure every selector in the Sigma rule matches observed telemetry."""
    # This ensures the rule is structurally valid YAML and parsable Sigma
    try:
        selectors = parse_selectors(rule_yaml)
    except Exception as ex:
        raise UngroundedRuleError(f"Invalid Sigma structure: {ex}")
        
    for sel in selectors:
        matched_any = False
        for e in events:
            val = getattr(e, sel.attr, None)
            if sel.matches_value(str(val) if val is not None else None):
                matched_any = True
                break
        if not matched_any:
            raise UngroundedRuleError(f"Hallucination detected: {sel.field} {sel.modifier} '{sel.value}' not found in telemetry.")

def generate_rule(events: List[NormalizedEvent], technique_id: str, provider: LLMProvider | None = None) -> str:
    """Synthesize a Sigma rule using the LLM, with fallback to deterministic local rules."""
    provider = provider or get_provider()
    
    # We must have process_name to generate anything grounded
    if not any(e.process_name for e in events):
        raise UngroundableTelemetryError("Cannot synthesize rule without process_name telemetry.")
        
    prompt = build_prompt(events)
    
    try:
        response_text = provider.complete(prompt)
        
        # Often LLMs wrap yaml in ```yaml ... ```
        if "```yaml" in response_text:
            response_text = response_text.split("```yaml")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        validate_grounding(response_text, events)
        
        # Enforce CASCABEL tags and candidate status
        rule = yaml.safe_load(response_text)
        rule['status'] = 'candidate'
        if 'tags' not in rule:
            rule['tags'] = []
        if f'attack.{technique_id.lower()}' not in rule['tags']:
            rule['tags'].append(f'attack.{technique_id.lower()}')
            
        return yaml.dump(rule, sort_keys=False)
        
    except (LLMUnavailableError, UngroundedRuleError):
        # Fallback to the safe, mathematically grounded deterministic generator
        return build_grounded_rule(events, technique_id)
