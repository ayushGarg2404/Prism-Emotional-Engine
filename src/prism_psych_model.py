from pydantic import BaseModel

class ValenceArousalModel(BaseModel):
    valence: float # Negative to Positive (-1.0 to 1.0)
    arousal: float # Low to High (-1.0 to 1.0)
    
    @classmethod
    def map_from_vector(cls, emotional_vector, text: str, gap_days: float):
        """
        Maps an EmotionalVector to the Valence-Arousal 2D space.
        Uses the vector's valence directly (-1 to 1 mapping from 0 to 1).
        Approximates Arousal using vitality and resilience.
        """
        # Map 0-1 to -1 to 1
        mapped_valence = (emotional_vector.valence * 2.0) - 1.0
        
        # Arousal is driven by vitality, chaos (1-agency), and word count pacing
        # Short rapid responses might be high arousal, or just exhaustion. This will be grounded later.
        arousal_base = emotional_vector.vitality
        if emotional_vector.agency < 0.5:
             # Low agency often correlates with reactive high arousal (anxiety) or complete collapse (depression)
             # Let's say high clarity = anxiety (arousal up), low clarity = depression (arousal down)
             if emotional_vector.clarity > 0.5:
                 arousal_base += 0.2
             else:
                 arousal_base -= 0.2
                 
        # Map 0-1 to -1 to 1
        mapped_arousal = (max(0.0, min(1.0, arousal_base)) * 2.0) - 1.0
        
        return cls(valence=mapped_valence, arousal=mapped_arousal)
    
    def get_discrete_emotion(self):
        """Maps continuous V-A space to basic discrete emotions."""
        if self.valence > 0.3 and self.arousal > 0.3: return "Excitement / Joy"
        if self.valence > 0.3 and self.arousal < -0.3: return "Calm / Contentment"
        if self.valence < -0.3 and self.arousal > 0.3: return "Anger / Frustration / Anxiety"
        if self.valence < -0.3 and self.arousal < -0.3: return "Sadness / Exhaustion / Depression"
        return "Neutral / Mixed"
