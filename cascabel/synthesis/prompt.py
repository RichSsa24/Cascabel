from typing import List
from cascabel.telemetry.schema import NormalizedEvent

def build_prompt(events: List[NormalizedEvent]) -> str:
    prompt = "You are an expert detection engineer. "
    prompt += "Generate a YAML detection rule using ONLY the following telemetry events. "
    prompt += "Do not hallucinate fields. The rule must fire if 'process_name' matches the telemetry.\n\n"
    
    prompt += "Events:\n"
    for e in events:
        prompt += f"- process_name: {e.process_name}\n"
        prompt += f"  command_line: {e.command_line}\n"
        
    return prompt
