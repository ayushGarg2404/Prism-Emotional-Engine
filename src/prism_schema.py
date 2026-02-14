from pydantic import BaseModel, Field, model_validator
from typing import Optional

class EmotionalVector(BaseModel):
    agency: float = Field(..., description="Causal Potency (0.0=Victim, 1.0=Architect)")
    vitality: float = Field(..., description="Bio-energetic Bandwidth")
    resilience: float = Field(..., description="Elasticity/Recovery capacity")
    clarity: float = Field(..., description="Semantic Resolution/Focus")
    stability: float = Field(..., description="Equilibrium")
    presence: float = Field(..., description="Temporal Anchoring")
    connection: float = Field(..., description="Relational Depth")
    empathy: float = Field(..., description="Affective Mirroring")
    harmony: float = Field(..., description="Internal Coherence")
    growth: float = Field(..., description="Syntropic Orientation")
    valence: float = Field(..., description="Affective Polarity (Despair to Euphoria)")

    @model_validator(mode='after')
    def validate_shadow_congruence(self) -> 'EmotionalVector':
        # Logic: If clarity is low but valence is high, it's likely a 'masking' event.
        # We automatically dampen the valence to reflect the lack of clarity.
        if self.clarity < 0.35 and self.valence > 0.75:
            self.valence *= 0.8  
        return self

class AuditResult(BaseModel):
    detected_masking: bool = Field(..., description="True if subtext contradicts literal text")
    dissonance_score: float = Field(..., description="Linguistic Drift (D): Conflict between words and meaning")
    viscosity_tag: str = Field(..., description="'Stuck', 'Flowing', or 'Breakthrough'")
    shadow_sentence: str = Field(..., description="The unspoken truth found in the subtext")
    reasoning: str = Field(..., description="The diagnostic explanation of the audit")

class PrismResponse(BaseModel):
    vector: EmotionalVector
    audit: AuditResult
    therapeutic_mirror: str = Field(..., description="Clinical, non-judgmental reflection of the shadow")