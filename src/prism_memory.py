import json
import os
import math
from datetime import datetime, timedelta

DB_FILE = "prism_vault.json"
RULES_FILE = "prism_constitution.json"

def calculate_trust_score(audit):
    """
    Calculates trust using a Sigmoid function of the Dissonance Score.
    High dissonance (drift) = Low Trust = Lower weight in memory.
    """
    # Access attribute directly from the Pydantic AuditResult object
    D = getattr(audit, 'dissonance_score', 0.5)
    
    # Sigmoid logic
    # If D is 0 (Congruent), Trust is ~1.0
    # If D is 1 (Masked), Trust is ~0.0
    trust = 1 / (1 + math.exp(10 * (D - 0.5)))
    
    # Apply Viscosity Penalty
    if getattr(audit, 'viscosity_tag', '') == "Stuck":
        trust *= 0.6 
        
    return round(max(0.1, trust), 2)

def save_entry(response_obj):
    """Saves the audit result to the vault with a trust weight."""
    history = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: history = json.load(f)
        except json.JSONDecodeError: history = []

    # response_obj is a PrismResponse instance
    trust_weight = calculate_trust_score(response_obj.audit)
    
    entry = response_obj.model_dump() # Convert Pydantic to Dict for JSON
    entry['_timestamp'] = datetime.now().isoformat()
    entry['_trust_weight'] = trust_weight
    
    history.append(entry)
    with open(DB_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    return trust_weight

def get_baseline():
    """Calculates the 7-day weighted moving average of the user's state."""
    if not os.path.exists(DB_FILE): return {"valence": 0.50, "agency": 0.50}
    
    try:
        with open(DB_FILE, 'r') as f: history = json.load(f)
    except json.JSONDecodeError: return {"valence": 0.50, "agency": 0.50}
    
    cutoff = datetime.now() - timedelta(days=7)
    recent = [x for x in history if datetime.fromisoformat(x['_timestamp']) > cutoff]
    
    if not recent: return {"valence": 0.50, "agency": 0.50}

    total_w = sum(x.get('_trust_weight', 1.0) for x in recent)
    if total_w == 0: return {"valence": 0.50, "agency": 0.50}

    avg_val = sum(x['vector']['valence'] * x.get('_trust_weight', 1.0) for x in recent) / total_w
    avg_agn = sum(x['vector']['agency'] * x.get('_trust_weight', 1.0) for x in recent) / total_w
    
    return {"valence": round(avg_val, 2), "agency": round(avg_agn, 2)}

def save_feedback(user_correction: str, audit):
    """
    Saves user corrections as new rules in the constitution.
    The rule's weight is determined by how 'aware' the user was during the audit.
    """
    trust_score = calculate_trust_score(audit)
    
    new_rule = {
        "rule": user_correction,
        "weight": trust_score,
        "tag": getattr(audit, 'viscosity_tag', 'Unknown'),
        "shadow_trigger": getattr(audit, 'shadow_sentence', ''),
        "timestamp": datetime.now().isoformat()
    }
    
    rules = []
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r') as f: rules = json.load(f)
        except json.JSONDecodeError: rules = []
    
    rules.append(new_rule)
    with open(RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=4)
        
    return trust_score

def load_rules():
    """Retreives the most recent high-weight rules to guide the Engine."""
    if not os.path.exists(RULES_FILE): return "No prior rules established."
    
    try:
        with open(RULES_FILE, 'r') as f: rules = json.load(f)
    except json.JSONDecodeError: return "Constitution file corrupted."

    # Sort by recentness and weight, take top 5
    # (Simple implementation: just take last 5 for context window efficiency)
    active_rules = rules[-5:]
    
    formatted_rules = []
    for r in active_rules:
        formatted_rules.append(f"- RULE: {r['rule']} (Authority Weight: {r['weight']})")
    
    return "\n".join(formatted_rules)