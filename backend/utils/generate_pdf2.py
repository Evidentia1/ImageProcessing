from fpdf import FPDF
from pathlib import Path
import re
import google.generativeai as genai
import os
from dotenv import load_dotenv

# ── Load Gemini API ──
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# ── Fonts ──
FONT_DIR = Path(__file__).parent / "fonts"
FONT_REGULAR = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"

# ── Emoji remover ──
_EMOJI_RE = re.compile("[" "\U0001F600-\U0001F64F" "\U0001F300-\U0001F5FF"
                       "\U0001F680-\U0001F6FF" "\U0001F1E0-\U0001F1FF"
                       "\u2600-\u26FF" "\u2700-\u27BF"
                       "\U0001F900-\U0001F9FF" "]+", flags=re.UNICODE)
def strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text or "")

# ── LLM Summary Generator ──
def generate_pdf_text_from_state(state: dict) -> str:
    prompt = f"""
You are an expert insurance claim summarizer.

Write a clean, professional summary in the following format for a PDF report:

1. **Claim Submission**
   - Summarize what the user submitted: text, image, type of issue, etc.

2. **Image & Label Analysis**
   - Summarize the labels detected.
   - Mention if labels match the claim context or not.

3. **EXIF & Policy Info**
   - Was image taken after policy start?
   - Any EXIF issues or mismatches?

4. **Weather Verification**
   - Was weather checked?
   - Did reported storm/natural calamity match real data?

5. **Misrepresentation Check**
   - Any signs of fake, misleading, or AI-generated images?

6. **Final Decision**
   - Was the claim approved, rejected, or flagged?
   - State clear reasoning.

Only include relevant data, and do not output raw JSON or raw dict.

Here is the data:
{state}
"""
    response = model.generate_content(prompt)
    return response.text

# ── PDF class ──
class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font("DejaVu", "", str(FONT_REGULAR), uni=True)
        self.add_font("DejaVu", "B", str(FONT_BOLD), uni=True)
        self.set_font("DejaVu", "", 12)
        self.add_page()

    def header(self):
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, "Insurance Claim Evaluation Report", ln=True, align="C")
        self.ln(10)

    def add_md_line(self, line: str):
        if line.strip().startswith("**") and line.strip().endswith("**"):
            self.set_font("DejaVu", "B", 13)
            title = line.strip().strip("*").strip()
            self.cell(0, 10, title, ln=True)
            self.ln(2)
        else:
            self.set_font("DejaVu", "", 11)
            self.multi_cell(0, 7, strip_emoji(line.strip()))
            self.ln(1)

# ── PDF Generator ──
def generate_pdf2(output_path: str, state: dict) -> str:
    summary_text = generate_pdf_text_from_state(state)

    pdf = PDFReport()
    for raw in summary_text.split("\n"):
        if raw.strip():
            pdf.add_md_line(raw)

    pdf.output(output_path)
    return output_path
