def evaluate_contradiction(semantic_valence: float, structural_cues: dict, baseline: dict, ingestion_meta: dict) -> bool:
    """
    Evaluates if a semantic/structural mismatch is a true contradiction (masking) 
    or just the user's baseline behavior.
    """
    is_positive_semantic = semantic_valence > 0.6
    
    # Structural cues: clipped pacing
    is_clipped = structural_cues.get("is_clipped", False)
    
    # Check inter_entry gap (exhaustion)
    gap_days = ingestion_meta.get("inter_entry_gap_days", 0)
    
    # If it's a positive tone but structurally clipped or anomalous
    if is_positive_semantic and is_clipped:
        if gap_days > 3.0:
            # Long gap + clipped positive response = likely exhaustion, not active masking/anxiety
            # Will not flag as a high-dissonance contradiction
            return False
            
        return True # True contradiction (highly deviating structural cue without explanation)
        
    return False

def interpret_soul_map(vector, subtext):
    print("\n" + "—"*60)
    print("   STRUCTURAL TOPOGRAPHY REPORT")
    print("—"*60)

    # 1. Analyze Peak Integrity (Valence)
    if vector.valence > 0.6:
        peak_desc = "Elevated Peak"
        peak_insight = "Your reported state is seeking high altitude."
    elif vector.valence < 0.4:
        peak_desc = "Submerged Crater"
        peak_insight = "The emotional terrain is currently recessed."
    else:
        peak_desc = "Mid-level Plateau"
        peak_insight = "The state is seeking equilibrium."

    # 2. Analyze Surface Tension (Agency)
    # Based on your visualizer: chaos_level = (1.0 - vector.agency) * 0.3
    if vector.agency > 0.8:
        tension = "Glassy/Smooth"
        tension_insight = "High agency is providing strong 'architectural control' over the experience."
    elif vector.agency < 0.4:
        tension = "Highly Jagged/Volatile"
        tension_insight = "Low agency is causing 'structural noise'; you are reacting to the terrain rather than building it."
    else:
        tension = "Rippled"
        tension_insight = "A balance of control and environmental influence."

    # 3. Analyze The Mask (Dissonance)
    if subtext.detected_masking:
        mask_status = "COLD / OCEANIC"
        mask_insight = "The 'Ocean' colormap indicates high dissonance. The peak is likely a 'mirage'—it stands tall but lacks a solid base."
    else:
        mask_status = "WARM / MAGMATIC"
        mask_insight = "The 'Magma' colormap suggests resonance. The heat in the center matches the height of the peak."

    # Final Summary
    print(f"● TOPOGRAPHY: {peak_desc} with {tension} surface tension.")
    print(f"● COLOR SIGNATURE: {mask_status}")
    print(f"\n[ARCHITECTURAL ANALYSIS]")
    print(f"  {peak_insight}")
    print(f"  {tension_insight}")
    print(f"  {mask_insight}")
    print("—"*60 + "\n")