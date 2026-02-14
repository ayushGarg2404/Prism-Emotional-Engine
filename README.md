# Prism-Emotional-Engine
A Shadow-Aware Affective Computing engine that uses Gemini 3 Flash to detect emotional dissonance and visualize internal states through 3D topographical "Soul Maps."
# 💎 Prism Emotional Engine v1.0
### Shadow-Aware Affective Computing & 3D Topographical Mapping

**Prism** is an advanced emotional diagnostics framework designed to identify the discrepancy between a user's literal narrative and their latent psychological state. By utilizing **Topographical Affective Mapping**, Prism transforms complex 11-dimensional emotional vectors into intuitive 3D landscapes.

---

## 🚀 The Core Innovation: Shadow-Aware Architecture
Unlike standard sentiment classifiers that only read surface-level data, Prism performs a **Cascaded Audit**:
1. **Linguistic Analysis:** Evaluates the 11-dimensional emotional vector (Agency, Vitality, Clarity, etc.).
2. **Dissonance Detection:** Identifies "Adversarial Defenses" such as minimization and future-tense deflection.
3. **The Shadow Sentence:** The AI generates a "hidden" sentence representing the user's authentic, unmasked internal state.

---

## 📊 Interpreting the Soul Map
The 3D visualization (built with Matplotlib) acts as a structural integrity report:

* **Gaussian Peak (Z-Axis):** Represents Valence Amplitude. A high peak indicates reported positivity.
* **Surface Tension (Noise):** Calculated as `(1.0 - Agency) * 0.3`. 
    * **Smooth Surfaces:** Indicate high agency and structural resonance.
    * **Jagged Spikes:** Indicate internal chaos, low agency, and emotional dissonance.
* **Color Mapping:** * `Magma` (Warm): Authentic resonance.
    * `Ocean` (Cold): Masked/Dissonant state detected.

---

## 🛠️ Installation & Usage

### 1. Requirements
Ensure you have Python 3.10+ installed. Install the necessary libraries:
```bash
pip install google-genai matplotlib numpy pydantic
