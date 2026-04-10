import json
import os
import math
from datetime import datetime, timedelta

DB_FILE = "prism_vault.json"
RULES_FILE = "prism_constitution.json"

def calculate_trust_score(audit, subtext):
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
    if getattr(subtext, 'viscosity_tag', '') == "Stuck":
        trust *= 0.6 
        
    return round(max(0.1, trust), 2)

def save_entry(response_obj, raw_text: str = "", metadata: dict = None):
    """Saves the audit result and metadata to the relational vault, and text to Vector store."""
    history = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: history = json.load(f)
        except json.JSONDecodeError: history = []

    trust_weight = calculate_trust_score(response_obj.audit, response_obj.subtext)
    
    entry = response_obj.model_dump()
    entry['_timestamp'] = datetime.now().isoformat()
    entry['_trust_weight'] = trust_weight
    
    if metadata:
        entry['_metadata'] = metadata

    history.append(entry)
    with open(DB_FILE, 'w') as f:
        json.dump(history, f, indent=2)
        
    # TODO 2026: Actual ChromaDB / Vector embedding saving goes here for Semantic retrieval
    return trust_weight

LORE_FILE = "prism_lore.json"

def get_baseline():
    """Calculates the Exponential Moving Average (EMA) baseline of the user's state."""
    default_baseline = {"valence": 0.50, "agency": 0.50, "last_entry_timestamp": None}
    if not os.path.exists(DB_FILE): return default_baseline
    
    try:
        with open(DB_FILE, 'r') as f: history = json.load(f)
    except json.JSONDecodeError: return default_baseline
    
    if not history: return default_baseline

    # Sort history chronologically
    history.sort(key=lambda x: datetime.fromisoformat(x['_timestamp']))
    last_timestamp = history[-1]['_timestamp']
    
    # Calculate EMA
    # EMA_today = Value_today * (alpha) + EMA_yesterday * (1 - alpha)
    alpha = 0.3 # Smoothing factor (30% weight to current day, 70% to historical trajectory)
    
    ema_val = history[0]['vector']['valence']
    ema_agn = history[0]['vector']['agency']
    
    for x in history[1:]:
        val = x['vector']['valence']
        agn = x['vector']['agency']
        
        # Apply time decay weight (adjusted by trust score)
        trust = x.get('_trust_weight', 1.0)
        adjusted_alpha = alpha * trust 
        
        ema_val = (val * adjusted_alpha) + (ema_val * (1 - adjusted_alpha))
        ema_agn = (agn * adjusted_alpha) + (ema_agn * (1 - adjusted_alpha))
        
    return {
        "valence": round(ema_val, 2), 
        "agency": round(ema_agn, 2),
        "last_entry_timestamp": last_timestamp
    }

def retrieve_lore_store():
    """
    Track A: The 'Lore' Store (Identity/Context).
    Stores facts, recurring topics, people, and personality traits.
    Used purely for contextual grounding.
    """
    return "Track A (Context/Lore): User relies on systems. Communicates directly."

def retrieve_semantic_history(current_text: str):
    """
    Track B: The 'Affective' Store.
    Simulates retrieval of past emotional vectors & shadow meanings from Vector DB.
    Provides transient state mapping (e.g., 'April 10: Deep feelings of inadequacy masked by anger').
    """
    return "Track B (Affective Memory): No semantically similar past emotional anomalies found."


def save_feedback(user_correction: str, audit, subtext):
    """
    Saves user corrections as new rules in the constitution.
    The rule's weight is determined by how 'aware' the user was during the audit.
    """
    trust_score = calculate_trust_score(audit, subtext)
    
    new_rule = {
        "type": "user_corrected",
        "rule": user_correction,
        "weight": trust_score,
        "tag": getattr(subtext, 'viscosity_tag', 'Unknown'),
        "shadow_trigger": getattr(subtext, 'shadow_sentence', ''),
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


def save_personality_observation(audit, subtext, raw_text: str = ""):
    """
    Auto-tracks a personality snapshot from every session into the constitution.
    This runs regardless of whether the user agrees or corrects the output.
    Builds a passive, evolving personality model over time.
    """
    vec = getattr(audit, 'vector', None)
    trust_score = calculate_trust_score(audit, subtext)
    
    # Summarise emotional tone from the vector
    valence_label = "positive" if (vec and vec.valence > 0.6) else "negative" if (vec and vec.valence < 0.4) else "neutral"
    agency_label  = "high-agency" if (vec and vec.agency > 0.6) else "low-agency" if (vec and vec.agency < 0.4) else "moderate-agency"
    
    observation = {
        "type": "auto_observed",
        "weight": round(trust_score * 0.6, 2),  # Auto-observations carry lower influence than direct corrections
        "tag": getattr(subtext, 'viscosity_tag', 'Unknown'),
        "shadow_sentence": getattr(subtext, 'shadow_sentence', ''),
        "subtle_indicator": getattr(subtext, 'subtle_indicator', ''),
        "emotional_tone": f"{valence_label}, {agency_label}",
        "dissonance_score": getattr(audit, 'dissonance_score', 0.5),
        "detected_masking": getattr(subtext, 'detected_masking', False),
        "timestamp": datetime.now().isoformat()
    }
    
    rules = []
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r') as f: rules = json.load(f)
        except json.JSONDecodeError: rules = []
    
    rules.append(observation)
    with open(RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=4)


def load_rules():
    """Retrieves a structured constitution: personality observations + user corrections."""
    if not os.path.exists(RULES_FILE): return "No prior personality patterns established."
    
    try:
        with open(RULES_FILE, 'r') as f: rules = json.load(f)
    except json.JSONDecodeError: return "Constitution file corrupted."
    
    if not rules: return "No prior personality patterns established."

    # Separate the two types
    corrections = [r for r in rules if r.get('type') == 'user_corrected']
    observations = [r for r in rules if r.get('type') == 'auto_observed']

    formatted_rules = []

    # Include up to 3 most recent and highest-weight personality observations
    top_obs = sorted(observations, key=lambda x: (x.get('weight', 0), x.get('timestamp', '')), reverse=True)[:3]
    if top_obs:
        formatted_rules.append("[PERSONALITY PATTERNS (auto-observed across sessions)]")
        for o in top_obs:
            formatted_rules.append(
                f"  • Emotional tone: {o.get('emotional_tone', 'unknown')} | "
                f"Viscosity: {o.get('tag', '?')} | "
                f"Masking: {o.get('detected_masking', False)} | "
                f"Unspoken theme: \"{o.get('shadow_sentence', '')}\""
            )

    # Include up to 3 most recent user corrections (highest trust)
    top_corr = sorted(corrections, key=lambda x: (x.get('weight', 0), x.get('timestamp', '')), reverse=True)[:3]
    if top_corr:
        formatted_rules.append("[USER CORRECTIONS (explicit feedback)]")
        for r in top_corr:
            formatted_rules.append(f"  • RULE: {r['rule']} (Authority Weight: {r['weight']})")

    return "\n".join(formatted_rules) if formatted_rules else "No prior personality patterns established."