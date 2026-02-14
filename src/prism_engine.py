import os
from google import genai
from google.genai import types
from prism_schema import PrismResponse

SYSTEM_INSTRUCTION = """
ESTABLISH: [PRISM CONSORTIUM ORCHESTRATOR]
MISSION: Perform a non-linear structural audit to detect the "Unreliable Narrator."

PHASE 1: THE INHABITANT (Subtextual Modeling)
- Listen for the 'Shadow Sentence' (the repressed emotional truth).
- Check for ADVERSARIAL DEFENSES (Over-explaining, Minimization, Future-tense deflection).

PHASE 2: THE SUPERVISOR (Mathematical Audit)
- Calculate 'Dissonance Score': The delta between literal text and the Shadow Sentence.
- Audit the 11D Vector: Ensure Valence isn't inflated if Clarity/Agency are low.

PHASE 3: THE MIRROR (Therapeutic Synthesis)
- Generate 'therapeutic_mirror'. Reflect discrepancies with clinical precision.
"""

def analyze_reflection(text: str, baseline: dict, constitution_str: str):
    # Ensure API Key is available
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    [HISTORICAL BASELINE]
    Core Affect Anchor: Valence {baseline['valence']:.2f}, Agency {baseline['agency']:.2f}
    
    [WEIGHTED CONSTITUTION - CUSTOM RULES]
    {constitution_str}
    
    [USER INPUT TO AUDIT]
    "{text}"
    
    [ORCHESTRATION]
    Execute Cascaded Audit. Return response in strictly aligned JSON.
    """
    
    # Using the high-reasoning model configuration
    response = client.models.generate_content(
        model="gemini-3-flash-preview", # Updated to a valid thinking model ID
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=PrismResponse,
            thinking_config=types.ThinkingConfig(thinking_level="high"),
            temperature=0.1 
        )
    )
    
    return response.parsed