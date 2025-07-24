import os, uuid
from pathlib import Path
from datetime import datetime
from typing import TypedDict, Optional

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END

from backend.config import GOOGLE_API_KEY
from backend.utils.exif_checker import validate_exif_logic
from backend.utils.vision_labels import get_image_labels
from backend.utils.summarizer   import summarize_claim
from backend.utils.key_info_extractor import extract_key_info
from backend.utils.misrep_detector    import detect_misrepresentation
from backend.utils.generate_pdf2      import generate_pdf2

# ── LLM setup ──────────────────────────────────────────
genai.configure(api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY)

# ── State schema ──────────────────────────────────────
class ClaimState(TypedDict, total=False):
    file_path: str
    user_text: str
    policy_data: dict

    # filled by nodes
    debug: list[str]
    exif: dict
    exif_date: Optional[str]
    gps_available: bool
    exif_vs_policy: str
    exif_vs_dol: str

    image_labels: str
    image_relevance: bool

    summary: str
    insight: str
    key_info: str
    misrep: dict
    misrep_found: bool
    weather_verified: Optional[bool]
    weather_summary: Optional[str]

    final_decision: str
    pdf_path: str

# ── Utility logger for debug steps ────────────────────
def log(state: ClaimState, msg: str):
    state.setdefault("debug", []).append(msg)

# ── Graph nodes ───────────────────────────────────────
def n_exif(state: ClaimState) -> ClaimState:
    state.update(validate_exif_logic(state["file_path"], state["policy_data"]))
    log(state, "✅ EXIF processed")
    return state

def n_labels(state: ClaimState) -> ClaimState:
    labels = get_image_labels(state["file_path"])
    state["image_labels"]   = ", ".join(labels) if labels else "No labels"
    state["image_relevance"] = any(l.lower() in state["user_text"].lower() for l in labels)
    log(state, f"✅ Labels: {state['image_labels']}")
    return state

def n_weather(state: ClaimState) -> ClaimState:
    if not state.get("natural_calamity"):
        state["weather_verified"] = False
        state["weather_summary"] = "Skipped: User marked claim not related to natural calamity."
        return state

    dol = state["policy_data"].get("dol")
    location = state["policy_data"].get("location")

    from backend.utils.weather_checker import verify_weather_event
    result = verify_weather_event(dol, location)

    state["weather_verified"] = result["verified"]
    state["weather_summary"] = result["summary"]

    return state

def n_summary(state: ClaimState) -> ClaimState:
    res = summarize_claim(state["user_text"], state["image_labels"].split(", "))
    state["summary"] = res["summary"]
    state["insight"] = res["insight"]
    log(state, "✅ Summary generated")
    return state

def n_keyinfo(state: ClaimState) -> ClaimState:
    state["key_info"] = extract_key_info(state["summary"])
    log(state, "✅ Key info extracted")
    return state

def n_misrep(state: ClaimState) -> ClaimState:
    state["misrep"] = detect_misrepresentation(state["key_info"], state["policy_data"])
    state["misrep_found"] = "yes" in state["misrep"].get("verdict", "").lower()
    log(state, "✅ Misrep checked")
    return state

def n_decision(state: ClaimState) -> ClaimState:
    tmpl = PromptTemplate(
        input_variables=[
            "summary","misrep","exif_date",
            "policy_start","dol","labels"
        ],
        template=(
            "Decision on insurance claim:\n\n"
            "📋 {summary}\n🚩 {misrep}\n📸 EXIF: {exif_date}\n"
            "📅 Policy: {policy_start}\n📆 DOL: {dol}\n🏷️ Labels: {labels}\n\n"
            "Return one line: APPROVE / REJECT / FLAG <reason>."
        )
    )
    resp = llm.invoke(tmpl.format(
        summary=state["summary"],
        misrep=state["misrep"],
        exif_date=state.get("exif_date","N/A"),
        policy_start=state["policy_data"].get("policy_date"),
        dol=state["policy_data"].get("dol"),
        labels=state["image_labels"]
    )).content.strip()

    if   resp.lower().startswith("approve"):
        state["final_decision"] = resp
    elif resp.lower().startswith("reject"):
        state["final_decision"] = resp
    else:
        state["final_decision"] = "FLAG: " + resp.split(":",1)[-1].strip()

    log(state, f"✅ Decision: {state['final_decision']}")
    return state

def n_pdf(state: ClaimState) -> ClaimState:
    out_dir = Path("frontend/data/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"claim_{uuid.uuid4().hex}.pdf"
    generate_pdf2(str(pdf_path), state)
    state["pdf_path"] = str(pdf_path)
    log(state, f"✅ PDF: {pdf_path}")
    return state

# ── Build LangGraph ───────────────────────────────────
flow = StateGraph(ClaimState)
flow.add_node("EXIF",            n_exif)
flow.add_node("LABELS",          n_labels)
flow.add_node("SUMMARY",         n_summary)
flow.add_node("KEYINFO",         n_keyinfo)
flow.add_node("MISREP",          n_misrep)
flow.add_node("WEATHER_CHECK",   n_weather)
flow.add_node("DECISION",        n_decision)
flow.add_node("PDF",             n_pdf)

flow.set_entry_point("EXIF")
flow.add_edge("EXIF",     "LABELS")
flow.add_edge("LABELS",   "SUMMARY")
flow.add_edge("SUMMARY",  "KEYINFO")
flow.add_edge("KEYINFO",  "MISREP")
flow.add_edge("MISREP",   "WEATHER_CHECK")
flow.add_edge("WEATHER_CHECK", "DECISION")
flow.add_edge("DECISION", "PDF")
flow.add_edge("PDF", END)

claim_agent = flow.compile()
