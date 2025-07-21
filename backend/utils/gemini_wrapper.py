import io
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Pick the newer multimodal model
_VISION_MODEL = "models/gemini-1.5-flash"

def gemini_vision_prompt(image_path: str, prompt: str) -> str:
    """
    Sends an image + prompt to Gemini-1.5-flash and returns plain-text response.
    """
    model = genai.GenerativeModel(_VISION_MODEL)

    with open(image_path, "rb") as img_file:
        image = Image.open(io.BytesIO(img_file.read()))

    response = model.generate_content([prompt, image])
    return response.text.strip()
