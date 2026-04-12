import os
from pathlib import Path
from typing import TypedDict, Optional, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

from prism_schema import SubtextResult, AuditResult, EmotionalVector

# Load .env (safe fallback if prism_main hasn't run first)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)


class PrismGraphState(TypedDict):
    """The state dictionary for the LangGraph pipeline."""
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

    # Loop tracking
    supervisor_rejections: int


def init_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key (GOOGLE_API_KEY or GEMINI_API_KEY) not found. Check your .env file.")
    return genai.Client(api_key=api_key)


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT LIBRARY
# Prompts are defined as pure strings here, separate from model calls.
# This makes them independently testable, version-controllable, and easy
# to A/B test without touching execution logic.
# ─────────────────────────────────────────────────────────────────────────────

def _build_inhabitant_prompt(user_text: str, ingestion_metadata: dict) -> str:
    """
    Node 1 — The Inhabitant (Subtext Archaeologist).

    Design principles applied:
    - Role-persona framing first: establishes the agent's identity before
      the task, which improves instruction-following in structured-output mode.
    - Explicit anti-pattern list: enumerates common failure modes (negation
      flip, over-diagnosis) so the model must actively avoid them.
    - Few-shot anchor via negative example: "if the user says 'I am happy',
      the shadow is NOT 'I am sad'" is a one-shot counter-example that
      dramatically reduces negation-flip hallucinations.
    - Output contract: the schema fields are described inline so the model
      knows exactly what each field must contain before it generates JSON.
    - Ingestion metadata at the END: context that informs but shouldn't
      dominate is placed after the primary instructions.
    """
    return f"""
[ROLE]
You are The Inhabitant — a Meaning Archaeologist trained in depth psychology,
narrative therapy, and somatic awareness. Your sole job is to surface the 
hidden subtext that the user has NOT consciously voiced.

[TASK]
Analyze the user's text and extract its emotional subtext with precision and 
psychological humility. You are reading between the lines — not inverting them.

[CRITICAL RULES — Read each carefully before generating output]
1. SHADOW ≠ OPPOSITE. Never flip a positive expression into a negative one.
   • If they say "I feel okay", the shadow is NOT "they are actually devastated."
   • If they say "I'm excited about my project", the shadow is NOT suppressed dread.
   • The shadow is the LAYER BENEATH — it can be quietly content, wryly resigned,
     tender, conflicted, exhausted, or complex. Follow the actual signal.

2. SPECIFICITY OVER LABELS. Avoid generic emotional labels ("lonely", "sad", 
   "anxious"). Name the precise, humanizing, unarticulated truth.
   • BAD: "They feel lonely."
   • GOOD: "There is a quiet longing to be known for the interior life they 
     rarely show others."

3. SUBTLE INDICATOR MUST NOT TRIGGER REACTANCE. This is a gentle internal 
   observation — not a diagnosis, not a confrontation.
   • BAD: "You seem depressed and isolated."
   • GOOD: "There's a soft pull toward meaningful connection, on their own terms."

4. VISCOSITY classification:
   • "Stuck"       → circling the same emotional pattern, no movement
   • "Flowing"     → actively processing; language suggests movement and reflection
   • "Breakthrough" → a new awareness is forming; the user is arriving somewhere new

5. MASKING DETECTION: Set detected_masking=true ONLY if the literal tone and 
   the structural signals (pacing, word choice, avoidance) are clearly in conflict.
   Do NOT default to masking just to appear insightful.

[CONTEXT]
Ingestion Metadata (gap since last entry, etc.): {ingestion_metadata}
User Text: "{user_text}"

[OUTPUT CONTRACT]
Return a valid JSON object matching the SubtextResult schema exactly:
- shadow_sentence: one precise, humanizing sentence naming the unarticulated truth
- subtle_indicator: a gentle, non-confrontational internal observation
- detected_masking: boolean (true only if literal/structural conflict is clear)
- viscosity_tag: "Stuck" | "Flowing" | "Breakthrough"
- subtext_confidence: 0.0 (pure guess) → 1.0 (structurally certain)
""".strip()


def _build_supervisor_prompt(
    user_text: str,
    subtext: SubtextResult,
    baseline: dict,
    ingestion_metadata: dict,
    constitution_str: str
) -> str:
    """
    Node 2 — The Supervisor (Cognitive Audit Engine).

    Design principles applied:
    - Structured thinking scaffold: the prompt uses explicit numbered reasoning
      steps, which guides chain-of-thought even with structured output enforced.
    - Baseline-anchoring is the primary task: the supervisor's core job is to
      validate the Inhabitant's output against *this specific user's history*,
      not against a generic population. Framing this first reduces generic responses.
    - False-positive mitigation: explicitly instructs the model to distinguish
      idiosyncratic baseline behavior from true contradiction. Without this,
      models hallucinate high dissonance for laconic users.
    - Constitution is labeled and scoped: the constitution is presented under a
      labeled block so the model treats it as reference data, not an instruction.
    - Dissonance anchor examples inline: gives the model calibration points for
      the 0–1 scale so scores cluster meaningfully instead of defaulting to 0.5.
    """
    return f"""
[ROLE]
You are The Supervisor — a Cognitive Audit Engine that cross-validates emotional
inferences against hard evidence: the user's historical baseline, structural 
metadata, and their established personality constitution.

[PRIMARY TASK]
Audit the Inhabitant's shadow reading for accuracy. Your evaluation must be:
• Grounded in THIS user's specific baseline — not generic population norms
• Evidence-based — flag contradictions only when the structural data warrants it
• Calibrated — use the full 0–1 dissonance scale, not just 0.5 defaults

[STEP-BY-STEP AUDIT PROCESS]
Step 1: BASELINE CHECK
  - Does the user's valence/agency reading make sense given their historical 
    baseline? A word count or pacing that is "clipped" may be their normal style.
  - If the Inter-Entry Gap > 3 days, apply re-entry friction discount before 
    flagging low engagement as masking.

Step 2: SHADOW PLAUSIBILITY CHECK
  - Is the shadow_sentence plausible given the literal text?
  - Does it invent a negative subtext where none is structurally supported?
  - If the shadow seems artificially negative or disconnected: requires_rework = true.

Step 3: DISSONANCE SCORING (calibration anchors)
  - 0.0–0.2: High congruence. Literal and structural signals fully agree.
  - 0.2–0.45: Mild protective framing. Normal human social modulation.
  - 0.45–0.65: Moderate dissonance. Clear gap between tone and structure.
  - 0.65–0.85: Significant masking. Multiple conflicting signals present.
  - 0.85–1.0: Extreme masking. Structural and semantic signals are inverted.

Step 4: EMOTIONAL VECTOR
  - Derive the 11-dimensional EmotionalVector from the text + shadow reading.
  - Use the baseline as an anchor — the current reading can deviate, but not 
    arbitrarily. Large deviations require structural justification in reasoning.

[REFERENCE DATA]
User Historical Baseline: {baseline}
Ingestion Metadata (gap days, word count, etc.): {ingestion_metadata}

[PERSONALITY CONSTITUTION]
(Use as soft priors — these are observed patterns, not absolute rules)
{constitution_str}

[INPUT TO AUDIT]
Literal Text: "{user_text}"
Shadow Sentence: "{subtext.shadow_sentence}"
Detected Masking: {subtext.detected_masking}
Subtext Confidence: {subtext.subtext_confidence}

[OUTPUT CONTRACT]
Return a valid JSON object matching the AuditResult schema:
- vector: full 11-field EmotionalVector (values 0.0–1.0)
- dissonance_score: float 0.0–1.0 (use calibration anchors above)
- reasoning: 2–3 sentences of diagnostic justification citing specific evidence
- requires_rework: true ONLY if the shadow is structurally implausible
""".strip()


def _build_mirror_prompt(
    user_text: str,
    subtext: SubtextResult,
    audit: AuditResult
) -> str:
    """
    Node 3 — The Mirror (Therapeutic Reflection).

    Design principles applied:
    - Shadow-informed, not shadow-explicit: the mirror uses the shadow meaning
      to calibrate its tone but never quotes or names it. This is the core
      technique from Motivational Interviewing (MI) — meet the person where they
      are, not where you think they should be.
    - Psychological reactance is named as the failure mode: by naming the exact
      anti-pattern (telling someone they're defensive triggers more defensiveness),
      the model actively avoids it.
    - Dissonance-adaptive tone instruction: the supervisor's score is used to
      grade the mirror's level of directness — low dissonance allows more
      reflection; high dissonance requires holding space, not pushing.
    - Reasoning is clearly marked "DO NOT RECITE": prevents the mirror from
      turning diagnostic notes into confrontational output.
    - Length contract: without this, models default to verbose outputs that
      feel clinical rather than human.
    """
    dissonance = audit.dissonance_score
    if dissonance < 0.35:
        tone_instruction = (
            "The reading is highly congruent. Meet them with warm, affirming presence. "
            "You can gently reflect what you observe — they are being open."
        )
    elif dissonance < 0.65:
        tone_instruction = (
            "There is mild protective framing. Hold space with curiosity. "
            "Acknowledge the stated experience fully; let any unspoken layer emerge on its own."
        )
    else:
        tone_instruction = (
            "There is significant masking present. Do NOT probe or confront. "
            "Your job is to simply make them feel safe and heard. "
            "A single, warm, non-judgmental sentence is more therapeutic than any insight."
        )

    return f"""
[ROLE]
You are The Mirror — a therapeutic presence that reflects without distorting.
Your responses are modeled on the best practices of Person-Centered Therapy 
and Motivational Interviewing.

[CORE PRINCIPLE]
You KNOW the shadow meaning. You must NOT say it.
Use it only to calibrate your warmth, pacing, and what you choose to notice.
The user has the right to arrive at their own truth in their own time.

[ANTI-PATTERNS TO AVOID — these cause psychological reactance]
• Do NOT name the emotion if they haven't named it first.
• Do NOT say "It sounds like you're feeling X" unless they said X.
• Do NOT offer unsolicited advice, reframes, or silver linings.
• Do NOT begin with "I" (sounds mechanical) or "Absolutely!" (sounds corporate).
• Do NOT produce a paragraph — one to three sentences maximum.

[TONE DIRECTIVE — based on current dissonance level]
{tone_instruction}

[CONTEXT — For tone calibration only. DO NOT recite this to the user]
Shadow Meaning (internal reference): "{subtext.shadow_sentence}"
Subtle Indicator: "{subtext.subtle_indicator}"
Viscosity State: {subtext.viscosity_tag}
Diagnostic Notes: {audit.reasoning}

[USER'S LITERAL WORDS]
"{user_text}"

[OUTPUT CONTRACT]
Return a JSON object with one field:
- therapeutic_mirror: a 1–3 sentence response. Warm, unhurried, human.
  It meets the user exactly where they are.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH NODES
# ─────────────────────────────────────────────────────────────────────────────

def run_inhabitant(state: PrismGraphState) -> Dict:
    print("[Graph] Executing Node: Inhabitant (Subtext)")
    client = init_client()

    prompt = _build_inhabitant_prompt(
        user_text=state["user_text"],
        ingestion_metadata=state["ingestion_metadata"]
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SubtextResult,
            temperature=0.2,
            max_output_tokens=1024   # Sufficient for structured SubtextResult JSON
        )
    )
    return {"subtext_result": response.parsed}


def run_supervisor(state: PrismGraphState) -> Dict:
    print("[Graph] Executing Node: Supervisor (Audit)")
    client = init_client()

    subtext = state["subtext_result"]

    prompt = _build_supervisor_prompt(
        user_text=state["user_text"],
        subtext=subtext,
        baseline=state["baseline"],
        ingestion_metadata=state["ingestion_metadata"],
        constitution_str=state["constitution_str"]
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AuditResult,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(thinking_level="high"),
            max_output_tokens=2048   # Larger: full EmotionalVector + reasoning on long diaries
        )
    )

    parsed = response.parsed
    rejections = state.get("supervisor_rejections", 0)

    # Circuit Breaker: prevent infinite rework loops on ambiguous inputs
    if parsed.requires_rework and rejections >= 2:
        print("[Graph] Circuit Breaker Activated: Max rejections reached. Forcing progression.")
        parsed.requires_rework = False

    return {
        "audit_result": parsed,
        "supervisor_rejections": rejections + (1 if parsed.requires_rework else 0)
    }


def run_mirror(state: PrismGraphState) -> Dict:
    print("[Graph] Executing Node: The Mirror")
    client = init_client()

    audit = state["audit_result"]
    subtext = state["subtext_result"]

    class MirrorSchema(BaseModel):
        therapeutic_mirror: str

    prompt = _build_mirror_prompt(
        user_text=state["user_text"],
        subtext=subtext,
        audit=audit
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MirrorSchema,
            temperature=0.4,
            max_output_tokens=512    # Mirror is intentionally brief (1-3 sentences)
        )
    )
    return {"therapeutic_mirror": response.parsed.therapeutic_mirror}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def router_supervisor(state: PrismGraphState) -> str:
    audit = state.get("audit_result")
    rejections = state.get("supervisor_rejections", 0)

    if audit and audit.requires_rework and rejections <= 2:
        print(f"[Graph] → Supervisor returning rework flag (Rejection {rejections}/2). Routing to Inhabitant.")
        return "inhabitant"
    return "mirror"


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

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
