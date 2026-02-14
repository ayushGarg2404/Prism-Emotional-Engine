import os
import sys
import traceback

# --- IMPORTS ---
from prism_memory import get_baseline, save_entry, load_rules, save_feedback
from prism_engine import analyze_reflection
from prism_interpreter import interpret_soul_map
# Optional: Visualization Import
try:
    from prism_visualizer import render_soul_map
except ImportError:
    def render_soul_map(v, a): 
        print("[SYSTEM] Visualizer module not found. Skipping Soul Map.")

# 1. API Configuration
# Replace with your actual key or ensure it is set in your OS environment
GEMINI_API_KEY = "AIzaSyBzLm3jFAb6ewwzu_pfuOn49o6Kk8yjvzQ" 
os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY 

def main():
    print("\n" + "="*60)
    print("   PRISM EMOTIONAL ENGINE v1.0 | SHADOW-AWARE ARCHITECTURE")
    print("="*60)
    
    # 1. RETRIEVE CONTEXT
    baseline = get_baseline()
    constitution = load_rules()
    
    print(f"\n[SYSTEM] Baseline Loaded: Valence {baseline['valence']:.2f} | Agency {baseline['agency']:.2f}")
    
    # Check if constitution is a string or list (handle empty case)
    rule_count = len(constitution.splitlines()) if constitution else 0
    print(f"[SYSTEM] Constitution Active: {rule_count} learning rules active.")
    
    # 2. USER INPUT
    user_text = input("\n> How are you feeling right now, really?\n> ")
    if not user_text.strip(): 
        print("[SYSTEM] Input empty. Terminating.")
        return
    
    print("\n[PRISM] Orchestrating Consortium Audit (Thinking: HIGH)...")
    
    try:
        # 3. INTELLIGENCE PHASE
        result = analyze_reflection(user_text, baseline, constitution)
        
        # Accessing validated Pydantic models
        vec = result.vector
        audit = result.audit 
        
        # 4. REPORT PHASE: THE MIRROR
        print("\n" + "—"*60)
        print(f"THE THERAPEUTIC MIRROR:\n\"{result.therapeutic_mirror}\"")
        print("—"*60)
        
        print(f"\n[INTERNAL DIAGNOSTICS]")
        print(f"● Shadow Sentence  : '{audit.shadow_sentence}'")
        print(f"● Dissonance Score : {audit.dissonance_score:.2f} (0=Congruent, 1=Masked)")
        print(f"● Viscosity Tag    : {audit.viscosity_tag}")
        print(f"● Core Vector      : Valence {vec.valence:.2f} | Agency {vec.agency:.2f} | Clarity {vec.clarity:.2f}")

        # 5. THE FEEDBACK LOOP
        print("\n" + "-"*30)
        feedback = input("Does this mirror your internal state? (Y/N or provide correction): ")
        
        if feedback.lower() not in ['y', 'yes', '']:
            # The feedback is weighted by the Dissonance Score.
            trust = save_feedback(feedback, audit)
            print(f"\n[SYSTEM] Constitution updated. Trust-Weight: {trust}")
            if trust < 0.4:
                print("(!) High Dissonance: Correction recorded with low influence on future audits.")
        else:
            print("\n[SYSTEM] Resonance confirmed. Pattern verified.")

        # 6. MEMORY PHASE
        weight = save_entry(result)
        print(f"[SYSTEM] Entry saved to Vault (Final Weight: {weight}).")
        
        # 7. VISUAL PHASE
        interpret_soul_map(vec, audit)
        render_soul_map(vec, audit)
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Engine Disruption: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()