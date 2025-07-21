from fpdf import FPDF
from pathlib import Path

# Font file paths (must be placed in /utils/fonts/)
FONT_REGULAR = Path(__file__).parent / "fonts/DejaVuSans.ttf"
FONT_BOLD = Path(__file__).parent / "fonts/DejaVuSans-Bold.ttf"

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        # Register fonts for Unicode & emoji support
        self.add_font("DejaVu", "", str(FONT_REGULAR), uni=True)
        self.add_font("DejaVu", "B", str(FONT_BOLD), uni=True)
        self.set_font("DejaVu", "", 12)

    def header(self):
        self.set_font("DejaVu", "B", 16)
        self.cell(0, 10, "📄 Insurance Claim Report", ln=True, align="C")
        self.ln(8)
#ssss
    def add_section(self, title, content):
        self.set_font("DejaVu", "B", 13)
        self.cell(0, 10, title, ln=True)
        self.set_font("DejaVu", "", 11)
        self.multi_cell(0, 10, content or "N/A")
        self.ln(3)

def generate_claim_pdf(output_path, summary, decision, labels, key_info, misrep):
    pdf = PDFReport()
    pdf.add_page()

    pdf.add_section("📝 Summary", summary)
    pdf.add_section("✅ Evaluation & Final Decision", decision)
    pdf.add_section("🖼️ Vision Labels", labels)
    pdf.add_section("🔑 Key Information Extracted", key_info)
    pdf.add_section("🚩 Misrepresentation Check", misrep)

    pdf.output(output_path)
    return output_path
