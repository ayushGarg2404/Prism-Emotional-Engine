from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any

class IngestionMetadata(BaseModel):
    inter_entry_gap_days: float = Field(0.0, description="Time passed since last journal entry (days)")
    audio_array: List[Any] = Field(default_factory=list, description="Reserved for future 2026 multimodal voice tracking")
    visual_array: List[Any] = Field(default_factory=list, description="Reserved for future 2026 multimodal facial tracking")

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
        if self.clarity < 0.35 and self.valence > 0.75:
            self.valence *= 0.8  
        return self

class SubtextResult(BaseModel):
    shadow_sentence: str = Field(..., description="The unspoken truth found in the subtext")
    subtle_indicator: str = Field(..., description="A gentle, non-intrusive observation of the hidden feelings that does not overreach or trigger negative reactions.")
    detected_masking: bool = Field(..., description="True if subtext contradicts literal text")
    viscosity_tag: str = Field(..., description="'Stuck', 'Flowing', or 'Breakthrough'")
    subtext_confidence: float = Field(..., description="Confidence in the shadow reading (0.0=Guess, 1.0=Certain)")

class AuditResult(BaseModel):
    vector: EmotionalVector
    dissonance_score: float = Field(..., description="Dissonance Score (0=Congruent, 1=Masked)")
    reasoning: str = Field(..., description="The diagnostic explanation of the audit")
    requires_rework: bool = Field(..., description="True if the subtext seems flawed or incomplete")

class PrismResponse(BaseModel):
    vector: EmotionalVector
    audit: AuditResult
    subtext: SubtextResult
    therapeutic_mirror: str = Field(..., description="Passive, validating reflection of the shadow meaning")