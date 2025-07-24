"""
Gemini-powered summarization + visual-relevance insight
───────────────────────────────────────────────────────
This module exposes a single public helper:

    summarize_claim(user_text: str, image_labels: list[str]) -> dict

Returned dict keys:
    summary            -> Two-sentence abstract of the claim
    label_match_score  -> 1-10 score (how well labels support text)
    insight            -> Short AI insight / missing info hint
"""

import os, json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# ✅ Load Gemini configuration via central config
from backend import config

# ── Initialize Gemini model with custom safety settings ──
_gemini = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash",
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH:       HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT:        HarmBlockThreshold.BLOCK_NONE,
    }
)

# ── Main helper function ─────────────────────────────
def summarize_claim(user_text: str, image_labels: list[str]) -> dict:
    """
    Returns a dict with `summary`, `label_match_score`, `insight`.
    - `label_match_score` is 1–10 (10 = perfect match).
    - `insight` is a <25-word AI hint on gaps or extra context needed.
    """
    labels_str = ", ".join(image_labels) if image_labels else "N/A"

    prompt = f"""
You are *ClaimAI*, an elite insurance-claim analyst.

USER_CLAIM_TEXT:
\"\"\"{user_text}\"\"\"

IMAGE_LABELS:
{labels_str}

TASKS
1. Rewrite a clear, two-sentence abstract of what the claimant says happened.
2. Rate how strongly the image labels support the claim on a scale of 1-10.
   (10 = labels unmistakably prove the claim; 1 = labels contradict it.)
3. If you see any gap or missing evidence (max 25 words), output it as an 'insight'.

Respond **strictly** as valid JSON in this exact schema:
{{
  "summary": "<two sentence summary>",
  "label_match_score": <integer 1-10>,
  "insight": "<short observation or '-' if none>"
}}
"""

    try:
        response = _gemini.generate_content(prompt)
        raw_text = response.text.strip()

        # Attempt JSON parse; fallback to raw
        try:
            parsed = json.loads(raw_text)
            return parsed
        except json.JSONDecodeError:
            return {
                "summary": raw_text,
                "label_match_score": 0,
                "insight": "Format error in AI response."
            }

    except Exception as exc:
        print("⚠️ Gemini summarization error:", exc)
        return {
            "summary": "Error: Could not summarize claim.",
            "label_match_score": 0,
            "insight": "Gemini API error."
        }
