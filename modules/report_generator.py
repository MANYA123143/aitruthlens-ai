"""
Report Generator Module for TruthLens AI.
Generates structured CSV and standalone PyMuPDF PDF fact-checking reports.
"""

import io
import datetime
import pandas as pd
from typing import List, Dict, Any
import pymupdf


def generate_csv_report(results: List[Dict[str, Any]], filename: str) -> str:
    """
    Transforms verification results into CSV string format.
    """
    rows = []
    for r in results:
        # Extract URLs
        sources_list = r.get("sources", [])
        urls = " | ".join([s.get("url", "") for s in sources_list if s.get("url")])
        source_titles = " | ".join([s.get("title", "") for s in sources_list if s.get("title")])

        rows.append({
            "Claim ID": r.get("claim_id"),
            "Page Number": r.get("page_number"),
            "Claim Type": r.get("claim_type"),
            "Original Claim": r.get("claim_text"),
            "Verification Status": r.get("verification_status"),
            "Evidence Strength": r.get("evidence_strength"),
            "Explanation": r.get("explanation"),
            "Corrected Information": r.get("corrected_info", "") or "N/A",
            "Key Evidence": r.get("evidence_text", "") or "N/A",
            "Source Titles": source_titles or "N/A",
            "Source URLs": urls or "N/A"
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def generate_pdf_report(
    results: List[Dict[str, Any]],
    source_filename: str,
    analysis_date: str = None
) -> bytes:
    """
    Generates a professional multi-page PDF Fact-Checking Report using PyMuPDF.
    Requires no extra external dependencies like reportlab or wkhtmltopdf.
    """
    if not analysis_date:
        analysis_date = datetime.datetime.now().strftime("%B %d, %Y - %H:%M:%S UTC")

    doc = pymupdf.open()
    
    # Calculate stats
    total_claims = len(results)
    verified_cnt = sum(1 for r in results if r.get("verification_status") == "VERIFIED")
    inaccurate_cnt = sum(1 for r in results if r.get("verification_status") == "INACCURATE")
    false_cnt = sum(1 for r in results if r.get("verification_status") == "FALSE")
    unverifiable_cnt = sum(1 for r in results if r.get("verification_status") == "UNVERIFIABLE")
    acc_pct = (verified_cnt / total_claims * 100) if total_claims > 0 else 0

    # Colors (RGB normalized 0.0 - 1.0)
    DARK_NAVY = (15/255, 23/255, 42/255)       # #0f172a
    PRIMARY_BLUE = (37/255, 99/255, 235/255)   # #2563eb
    TEXT_DARK = (30/255, 41/255, 59/255)       # #1e293b
    TEXT_MUTED = (100/255, 116/255, 139/255)   # #64748b
    BG_LIGHT = (248/255, 250/255, 252/255)     # #f8fafc
    BORDER_COLOR = (226/255, 232/255, 240/255) # #e2e8f0

    STATUS_COLORS = {
        "VERIFIED": (16/255, 185/255, 129/255),    # #10b981
        "INACCURATE": (245/255, 158/255, 11/255),  # #f59e0b
        "FALSE": (239/255, 68/255, 68/255),        # #ef4444
        "UNVERIFIABLE": (107/255, 114/255, 128/255)# #6b7280
    }

    # Cover / Header Page
    page = doc.new_page(width=595, height=842) # A4 format
    y = 50

    # Top Brand Bar
    page.draw_rect(pymupdf.Rect(0, 0, 595, 10), color=None, fill=PRIMARY_BLUE)

    # Title & Subtitle
    page.insert_text((50, y + 20), "TruthLens AI", fontsize=24, color=DARK_NAVY)
    page.insert_text((50, y + 38), "Intelligent PDF Fact-Checking & Verification Report", fontsize=12, color=PRIMARY_BLUE)
    page.draw_line((50, y + 48), (545, y + 48), color=BORDER_COLOR, width=1)
    
    y += 70
    page.insert_text((50, y), f"Analyzed Document: {source_filename}", fontsize=11, color=TEXT_DARK)
    page.insert_text((50, y + 16), f"Generated Date: {analysis_date}", fontsize=10, color=TEXT_MUTED)
    page.insert_text((50, y + 32), f"Total Claims Audited: {total_claims}", fontsize=10, color=TEXT_MUTED)
    page.insert_text((350, y + 32), f"Document Accuracy Proportion: {acc_pct:.1f}%", fontsize=10, color=PRIMARY_BLUE)

    y += 55

    # Executive Summary Card
    page.draw_rect(pymupdf.Rect(50, y, 545, y + 70), color=BORDER_COLOR, fill=BG_LIGHT)
    
    # 4 Status Mini-boxes
    col_w = (545 - 50) / 4
    boxes = [
        ("VERIFIED", verified_cnt, STATUS_COLORS["VERIFIED"]),
        ("INACCURATE", inaccurate_cnt, STATUS_COLORS["INACCURATE"]),
        ("FALSE", false_cnt, STATUS_COLORS["FALSE"]),
        ("UNVERIFIABLE", unverifiable_cnt, STATUS_COLORS["UNVERIFIABLE"]),
    ]

    for idx, (label, count, col) in enumerate(boxes):
        bx = 50 + (idx * col_w)
        page.insert_text((bx + 15, y + 25), str(count), fontsize=20, color=col)
        page.insert_text((bx + 15, y + 45), label, fontsize=9, color=TEXT_MUTED)

    y += 95
    page.insert_text((50, y), "Detailed Claim-by-Claim Verification Audit", fontsize=14, color=DARK_NAVY)
    page.draw_line((50, y + 8), (545, y + 8), color=BORDER_COLOR, width=1)
    y += 25

    def check_page_overflow(current_y: float, needed_height: float) -> float:
        nonlocal page
        if current_y + needed_height > 780:
            page = doc.new_page(width=595, height=842)
            page.draw_rect(pymupdf.Rect(0, 0, 595, 10), color=None, fill=PRIMARY_BLUE)
            # Footer / Header
            page.insert_text((50, 40), f"TruthLens AI Audit Report — {source_filename}", fontsize=8, color=TEXT_MUTED)
            page.draw_line((50, 48), (545, 48), color=BORDER_COLOR, width=0.5)
            return 65.0
        return current_y

    for res in results:
        cid = res.get("claim_id", 0)
        pnum = res.get("page_number", 1)
        ctype = res.get("claim_type", "Statistic")
        status = res.get("verification_status", "UNVERIFIABLE").upper()
        claim_text = res.get("claim_text", "")
        explanation = res.get("explanation", "")
        corrected = res.get("corrected_info")
        sources = res.get("sources", [])
        
        box_color = STATUS_COLORS.get(status, STATUS_COLORS["UNVERIFIABLE"])

        # Check space needed for claim card
        y = check_page_overflow(y, 130)

        # Draw card container
        page.draw_rect(pymupdf.Rect(50, y, 545, y + 115), color=BORDER_COLOR, fill=(1, 1, 1))
        # Left status highlight stripe
        page.draw_rect(pymupdf.Rect(50, y, 56, y + 115), color=None, fill=box_color)

        # Claim header & badge
        page.insert_text((65, y + 16), f"Claim #{cid}  |  PDF Page {pnum}  |  Type: {ctype}", fontsize=9, color=TEXT_MUTED)
        page.insert_text((440, y + 16), f"[{status}]", fontsize=10, color=box_color)

        # Claim statement text (wrap or truncate gently)
        trimmed_claim = (claim_text[:120] + "...") if len(claim_text) > 120 else claim_text
        page.insert_text((65, y + 33), f"\"{trimmed_claim}\"", fontsize=10, color=TEXT_DARK)

        # Explanation
        trimmed_expl = (explanation[:170] + "...") if len(explanation) > 170 else explanation
        page.insert_text((65, y + 52), f"Verdict Analysis: {trimmed_expl}", fontsize=8.5, color=TEXT_MUTED)

        # Corrected info if applicable
        if corrected and str(corrected).strip() and str(corrected).strip().lower() != "none":
            page.insert_text((65, y + 70), f"Corrected Fact: {str(corrected)[:110]}", fontsize=8.5, color=(220/255, 38/255, 38/255))
        else:
            page.insert_text((65, y + 70), f"Evidence Strength: {res.get('evidence_strength', 'Medium')}", fontsize=8.5, color=TEXT_MUTED)

        # Source URLs
        if sources:
            first_url = sources[0].get("url", "")
            trimmed_url = (first_url[:75] + "...") if len(first_url) > 75 else first_url
            page.insert_text((65, y + 90), f"Source Ref: {trimmed_url}", fontsize=8, color=PRIMARY_BLUE)
        else:
            page.insert_text((65, y + 90), "Source Ref: No external source verified this specific statement.", fontsize=8, color=TEXT_MUTED)

        y += 125

    # Footer on last page
    page.insert_text((50, 810), f"Generated by TruthLens AI | Document Verification System", fontsize=8, color=TEXT_MUTED)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
