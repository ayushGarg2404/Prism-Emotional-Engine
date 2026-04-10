import os
from typing import TypedDict, Optional, Dict, Any
from google import genai
from google.genai import types
from pydantic import BaseModel

from prism_schema import SubtextResult, AuditResult, EmotionalVector

class PrismGraphState(TypedDict):
    """The state dictionary for our LangGraph graph."""
    user_text: str
    baseline: Dict[str, Any]
    constitution_str: str
    ingestion_metadata: Dict[str, Any]
    
    # Populated by Subtext Agent
    subtext_result: Optional[SubtextResult]
    
    # Populated by Supervisor Agent
    audit_result: Optional[AuditResult]
    
    # Populated by Mirror Agent
    therapeutic_mirror: Optional[str]
    
    # Tracking loops
    supervisor_rejections: int

def init_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key (GOOGLE_API_KEY or GEMINI_API_KEY) not found.")
    return genai.Client(api_key=api_key)

# Node 1: The Inhabitant (Subtext Agent)
def run_inhabitant(state: PrismGraphState) -> Dict:
    print("[Graph] Executing Node: Inhabitant (Subtext)")
    client = init_client()
    
    prompt = f"""
    [MISSION: THE INHABITANT — MEANING ARCHAEOLOGIST]
    Your job is NOT to restate what the user said, and NOT to invent a pessimistic or negative version of their words.
    Your job is to surface the hidden meaning, the subtext they haven't consciously voiced.

    RULES:
    1. The 'Shadow Sentence' is the unspoken core truth beneath the surface — it may be hopeful, quietly content, wryly resigned, conflicted, tender, exhausted, or something more complex. It follows the ACTUAL emotional signal in the text, not a default-negative interpretation.
    2. NEVER flip a positive statement into a negative one just to look "insightful" (e.g., if the user says "I am happy", the shadow is NOT "but actually I am sad"). Look for the layer *beneath* the stated emotion, not the opposite of it.
    3. Ask: What is this person carrying that they haven't named? What is hinted at by word choice, pacing, what they avoided saying, or what they emphasized?
    4. The shadow sentence should be a single, precise, humanizing sentence that names the unarticulated truth.
    5. Also generate a 'subtle_indicator'—a gentle, non-intrusive internal observation of these hidden feelings. It must NOT overreach or trigger defensive reactions (e.g., instead of "You are lonely", say "There's a quiet pull toward being seen or heard").
    6. Viscosity Tag: Assess emotional flow — is this person 'Stuck' (circling the same pattern), 'Flowing' (processing well), or 'Breakthrough' (a new awareness forming)?

    Ingestion Info: {state['ingestion_metadata']}
    User Text: "{state['user_text']}"
    """
    
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SubtextResult,
            temperature=0.2 
        )
    )
    return {"subtext_result": response.parsed}

# Node 2: The Supervisor (Mathematical & Deductive Audit)
def run_supervisor(state: PrismGraphState) -> Dict:
    print("[Graph] Executing Node: Supervisor (Audit)")
    client = init_client()
    
    subtext = state["subtext_result"]
    
    prompt = f"""
    [MISSION: THE SUPERVISOR (Cognitive Engine)]
    Audit the subtext retrieved against the user's specific baseline.
    Avoid false positive contradictions: if pacing is clipped but matches their baseline average pacing, it is NOT a contradiction.
    If the Subtext is wildly off or impossible based on the baseline, set 'requires_rework' to true.
    
    User Baseline (Historical context): {state['baseline']}
    Ingestion Metadata (Gap days, word count, etc): {state['ingestion_metadata']}
    Constitution:
    {state['constitution_str']}
    
    Literal Text: "{state['user_text']}"
    Shadow Sentence: "{subtext.shadow_sentence}"
    Detected Masking: {subtext.detected_masking}
    """
    
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AuditResult,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(thinking_level="high")
        )
    )
    
    parsed = response.parsed
    rejections = state.get("supervisor_rejections", 0)
    
    # Circuit Breaker: Safeguard against infinite cognitive loops
    # If the text is highly ambiguous and requires_rework is triggered multiple times,
    # we forcefully break the loop and proceed to parsing the mirror.
    if parsed.requires_rework and rejections >= 2:
        print("[Graph] Circuit Breaker Activated: Maximum rejections reached. Forcing progression.")
        parsed.requires_rework = False
        
    return {
        "audit_result": parsed,
        "supervisor_rejections": rejections + (1 if parsed.requires_rework else 0)
    }

# Node 3: The Mirror
def run_mirror(state: PrismGraphState) -> Dict:
    print("[Graph] Executing Node: The Mirror")
    client = init_client()
    
    audit = state["audit_result"]
    subtext = state["subtext_result"]
    
    # We just need a string back
    class MirrorSchema(BaseModel):
        therapeutic_mirror: str
        
    prompt = f"""
    [MISSION: THE MIRROR]
    Do not proactively diagnose the user. Telling someone "You seem highly defensive right now" triggers psychological reactance.
    You must QUIETLY use the shadow meaning to adjust your own tone. Provide a validating response that meets them where they are.
    Acknowledge the situation without naming the emotion explicitly unless they named it first.
    
    Literal Text: "{state['user_text']}"
    Shadow Sentence / Unstated Truth: "{subtext.shadow_sentence}"
    Diagnostics Reference (For your tone adjustment, DO NOT recite this to the user): {audit.reasoning}
    """
    
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MirrorSchema,
            temperature=0.4
        )
    )
    return {"therapeutic_mirror": response.parsed.therapeutic_mirror}

def router_supervisor(state: PrismGraphState) -> str:
    audit = state.get("audit_result")
    rejections = state.get("supervisor_rejections", 0)
    
    # Strict Circuit breaker routing check
    if audit and audit.requires_rework and rejections <= 2:
        print(f"[Graph] -> Supervisor returning rework flag (Rejection {rejections}/2). Routing to Inhabitant.")
        return "inhabitant"
    return "mirror"

from langgraph.graph import StateGraph, END
def build_graph():
    builder = StateGraph(PrismGraphState)
    builder.add_node("inhabitant", run_inhabitant)
    builder.add_node("supervisor", run_supervisor)
    builder.add_node("mirror", run_mirror)
    
    builder.set_entry_point("inhabitant")
    builder.add_edge("inhabitant", "supervisor")
    
    builder.add_conditional_edges(
        "supervisor", 
        router_supervisor,
        {"inhabitant": "inhabitant", "mirror": "mirror"}
    )
    
    builder.add_edge("mirror", END)
    
    return builder.compile()
