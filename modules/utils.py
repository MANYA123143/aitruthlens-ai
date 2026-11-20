"""
Utility functions, data models, and helper methods for TruthLens AI.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import streamlit as st
import os


class ExtractedClaim(BaseModel):
    """Data model representing a single factual claim extracted from PDF."""
    claim_id: int
    claim_text: str
    claim_type: str = "Statistic"  # Statistic / Financial / Technical / Date / Other
    numerical_value: Optional[str] = None
    unit: Optional[str] = None
    reference_year: Optional[str] = None
    page_number: int = 1


class SourceEvidence(BaseModel):
    """Source reference with live web metadata."""
    title: str = "Web Source"
    url: str = ""
    publication_date: Optional[str] = None
    snippet: Optional[str] = None


class VerificationResult(BaseModel):
    """Verification output for a factual claim."""
    claim_id: int
    claim_text: str
    claim_type: str
    page_number: int
    verification_status: str  # VERIFIED, INACCURATE, FALSE, UNVERIFIABLE
    explanation: str
    corrected_info: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_strength: str = "Medium"  # High / Medium / Low
    sources: List[SourceEvidence] = Field(default_factory=list)


def get_gemini_api_key() -> Optional[str]:
    """
    Safely retrieve Gemini API Key from Streamlit Secrets or Environment Variables.
    Never crashes if not found; returns None so caller can handle gracefully.
    """
    # 1. Check Streamlit secrets
    try:
        if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            return st.secrets["GEMINI_API_KEY"].strip()
    except Exception:
        pass

    # 2. Check environment variables
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    return None


def get_status_badge(status: str) -> str:
    """Returns styled HTML badge for claim verification status."""
    status_upper = status.upper().strip()
    if status_upper == "VERIFIED":
        return '<span style="background-color:#10b981;color:#ffffff;padding:4px 10px;border-radius:12px;font-weight:600;font-size:0.82rem;">VERIFIED</span>'
    elif status_upper == "INACCURATE":
        return '<span style="background-color:#f59e0b;color:#ffffff;padding:4px 10px;border-radius:12px;font-weight:600;font-size:0.82rem;">INACCURATE</span>'
    elif status_upper == "FALSE":
        return '<span style="background-color:#ef4444;color:#ffffff;padding:4px 10px;border-radius:12px;font-weight:600;font-size:0.82rem;">FALSE</span>'
    else:
        return '<span style="background-color:#6b7280;color:#ffffff;padding:4px 10px;border-radius:12px;font-weight:600;font-size:0.82rem;">UNVERIFIABLE</span>'


def get_status_color(status: str) -> str:
    """Return hex color code associated with verification status."""
    status_upper = status.upper().strip()
    if status_upper == "VERIFIED":
        return "#10b981"  # Emerald green
    elif status_upper == "INACCURATE":
        return "#f59e0b"  # Amber orange
    elif status_upper == "FALSE":
        return "#ef4444"  # Red
    else:
        return "#6b7280"  # Neutral grey
