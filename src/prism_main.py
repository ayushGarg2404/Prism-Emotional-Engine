import os
import sys
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from /src).
# override=False means an already-set OS env var always wins (safe for CI/CD).
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=False)

# --- IMPORTS ---

from datetime import datetime
from prism_memory import get_baseline, save_entry, load_rules, save_feedback, save_personality_observation
from prism_engine import analyze_reflection
from prism_interpreter import interpret_soul_map
from prism_ingestion import PrismIngestion
# Optional: Visualization Import
try:
    from prism_visualizer import render_soul_map
except ImportError:
    def render_soul_map(v, a): 
        print("[SYSTEM] Visualizer module not found. Skipping Soul Map.")

# 1. API Configuration
# Replace with your actual key or ensure it is set in your OS environment
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY or "your_gemini_api_key_here" in GEMINI_API_KEY:
    print("\n" + "!"*60)
    print("[CRITICAL ERROR] API Key Missing or Placeholder Detected.")
    print("Please open the .env file and paste your real key:")
    print(f"Path: {Path(__file__).resolve().parent.parent / '.env'}")
    print("!"*60)
    sys.exit(1)

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
    
    # 2. USER INPUT — multiline diary mode
    # User types freely across as many lines as needed.
    # Submit with a blank line (press Enter on an empty line) or Ctrl+Z + Enter (Windows EOF).
    print("\n" + "─"*60)
    print("  Write freely. Press ENTER twice (or Ctrl+Z) when done.")
    print("─"*60)
    print("> How are you feeling right now, really?\n")

    lines = []
    try:
        while True:
            line = input()
            if line == "":          # blank line = intentional submit
                if lines:           # only stop if something was written
                    break
            else:
                lines.append(line)
    except EOFError:                # Ctrl+Z (Windows) / Ctrl+D (Unix) = hard submit
        pass

    user_text = "\n".join(lines).strip()

    if not user_text:
        print("[SYSTEM] Input empty. Terminating.")
        return

    word_count = len(user_text.split())
    char_count = len(user_text)
    print(f"\n[SYSTEM] Entry captured — {word_count} words / {char_count} characters.")
        
    ingestion = PrismIngestion()
    ingestion_metadata = ingestion.process_entry("user_1", user_text, datetime.now().isoformat(), baseline).model_dump()
    
    print("\n[PRISM] Orchestrating Consortium Audit (Thinking: HIGH)...")
    
    try:
        # 3. INTELLIGENCE PHASE
        result = analyze_reflection(user_text, baseline, constitution, ingestion_metadata)
        
        # Accessing validated Pydantic models
        vec = result.vector
        audit = result.audit 
        subtext = result.subtext
        
        # 4. REPORT PHASE: THE MIRROR
        print("\n" + "—"*60)
        print(f"THE THERAPEUTIC MIRROR:\n\"{result.therapeutic_mirror}\"")
        print("—"*60)
        
        print(f"\n[INTERNAL DIAGNOSTICS]")
        print(f"● Subtle Indicator : '{subtext.subtle_indicator}'")
        print(f"● Dissonance Score : {audit.dissonance_score:.2f} (0=Congruent, 1=Masked)")
        print(f"● Viscosity Tag    : {subtext.viscosity_tag}")
        print(f"● Core Vector      : Valence {vec.valence:.2f} | Agency {vec.agency:.2f} | Clarity {vec.clarity:.2f}")

        # 5. ALWAYS TRACK PERSONALITY — constitution learns from every session
        save_personality_observation(audit, subtext, raw_text=user_text)
        print("[SYSTEM] Personality observation recorded in Constitution.")

        # 6. THE FEEDBACK LOOP
        print("\n" + "-"*30)
        feedback = input("Does this mirror your internal state? (Y/N or provide correction): ")
        
        if feedback.lower() not in ['y', 'yes', '']:
            # The feedback is weighted by the Dissonance Score.
            trust = save_feedback(feedback, audit, subtext)
            print(f"\n[SYSTEM] Constitution updated. Trust-Weight: {trust}")
            if trust < 0.4:
                print("(!) High Dissonance: Correction recorded with low influence on future audits.")
        else:
            print("\n[SYSTEM] Resonance confirmed. Pattern verified.")

        # 7. MEMORY PHASE
        weight = save_entry(result, raw_text=user_text, metadata=ingestion_metadata)
        print(f"[SYSTEM] Entry saved to Vault (Final Weight: {weight}).")
        
        # 8. VISUAL PHASE
        interpret_soul_map(vec, subtext)
        render_soul_map(vec, subtext)
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Engine Disruption: {e}")
        traceback.print_exc()

if __name__ == "__main__":

    main()
