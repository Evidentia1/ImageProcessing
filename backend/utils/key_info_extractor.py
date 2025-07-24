import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from backend.config import GOOGLE_API_KEY  # 👈 From config.py

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize model with relaxed safety
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash",
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

# Key info extractor
def extract_key_info(text: str) -> str:
    prompt = f"""
Extract key claim information from the following text:

{text}

Return:
- Incident Date
- Damaged Items/Property
- Claimed Amounts (if stated)
- Cause of Damage
- Supporting Documents (if mentioned)
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("⚠️ Gemini key info extraction error:", e)
        return "Error: Could not extract key information."
