"""
Claim Extractor Module using Google Gemini API (google-genai SDK).
Extracts strictly verifiable factual assertions with numerical values, statistics,
dates, and financial metrics, while rejecting subjective or marketing claims.
"""

import json
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from modules.utils import ExtractedClaim


EXTRACTION_PROMPT = """You are a strict, world-class factual claim extraction engine for TruthLens AI.
Analyze the following text extracted from a PDF document (with page labels).

Extract verifiable factual assertions. Specifically identify:
- Numerical statistics and percentages
- Financial figures, revenue, market-size claims
- GDP and economic data
- Dates, timelines, and milestones
- Scientific and technical statements
- Company and product factual assertions
- Research findings and survey data
- Market forecasts and performance metrics

DO NOT EXTRACT:
- Subjective descriptions or opinions (e.g. "our company is the best")
- Marketing fluff or vague slogans
- Generic truisms or broad predictions that cannot be verified against historical or statistical data
- Duplicate statements of the same fact

Return a clean, valid JSON array of objects. Each object MUST strictly follow this JSON schema:
[
  {
    "claim_id": 1,
    "claim_text": "Original concise factual statement",
    "claim_type": "Statistic / Financial / Technical / Date / Other",
    "numerical_value": "Extracted value if applicable, or null",
    "unit": "Percentage / USD / INR / People / Other, or null",
    "reference_year": "Year if mentioned, or null",
    "page_number": 1
  }
]

Maximum claims to return: {max_claims}.
Preserve the exact page_number where the claim appeared in the source text.
Return ONLY raw JSON. Do not include markdown code block syntax (no ```json or ```).
"""


def extract_claims_from_text(
    pages_data: List[Dict[str, Any]],
    api_key: str,
    model_name: str = "gemini-2.5-flash",
    max_claims: int = 15
) -> Dict[str, Any]:
    """
    Extracts verifiable claims from document text using Gemini.
    Handles chunking if the document is large.
    """
    if not api_key:
        return {
            "success": False,
            "error": "Gemini API key is missing. Please provide a valid Gemini API Key in the sidebar or Streamlit secrets.",
            "claims": []
        }

    # Aggregate text with page markers
    doc_slices = []
    for page in pages_data:
        p_num = page.get("page_number", 1)
        p_text = page.get("text", "").strip()
        if p_text:
            doc_slices.append(f"[PAGE {p_num}]\n{p_text}")

    if not doc_slices:
        return {
            "success": False,
            "error": "No readable text content found to extract claims from.",
            "claims": []
        }

    combined_text = "\n\n".join(doc_slices)
    # Trim to 25,000 characters if exceptionally large to ensure fast, free-tier compliance
    if len(combined_text) > 25000:
        combined_text = combined_text[:25000] + "\n...[Content truncated for processing]"

    prompt = EXTRACTION_PROMPT.replace("{max_claims}", str(max_claims)) + f"\n\nDOCUMENT TEXT:\n{combined_text}"

    try:
        client = genai.Client(api_key=api_key)
        
        # We request structured JSON output
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

        raw_response = response.text or ""
        
        # Clean response string if backticks slipped in
        clean_json_str = raw_response.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:]
        elif clean_json_str.startswith("```"):
            clean_json_str = clean_json_str[3:]
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-3]
        clean_json_str = clean_json_str.strip()

        parsed_json = json.loads(clean_json_str)
        if not isinstance(parsed_json, list):
            if isinstance(parsed_json, dict) and "claims" in parsed_json:
                parsed_json = parsed_json["claims"]
            else:
                parsed_json = [parsed_json]

        # Validate and deduplicate claims
        validated_claims: List[ExtractedClaim] = []
        seen_texts = set()

        for idx, item in enumerate(parsed_json, start=1):
            if not isinstance(item, dict):
                continue
            text = item.get("claim_text", "").strip()
            if not text:
                continue
            # Normalize text for deduplication
            normalized_key = re.sub(r'\s+', ' ', text.lower())
            if normalized_key in seen_texts:
                continue
            seen_texts.add(normalized_key)

            claim = ExtractedClaim(
                claim_id=idx,
                claim_text=text,
                claim_type=item.get("claim_type") or "Statistic",
                numerical_value=str(item.get("numerical_value")) if item.get("numerical_value") is not None else None,
                unit=str(item.get("unit")) if item.get("unit") is not None else None,
                reference_year=str(item.get("reference_year")) if item.get("reference_year") is not None else None,
                page_number=int(item.get("page_number", 1))
            )
            validated_claims.append(claim)
            if len(validated_claims) >= max_claims:
                break

        return {
            "success": True,
            "error": None,
            "claims": [c.model_dump() for c in validated_claims]
        }

    except json.JSONDecodeError as jde:
        return {
            "success": False,
            "error": f"Failed to parse structured claim extraction response from Gemini: {str(jde)}",
            "claims": []
        }
    except Exception as e:
        err_msg = str(e)
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            err_msg = "Gemini API free quota or rate limit exceeded. Please wait a moment and retry."
        elif "API_KEY_INVALID" in err_msg or "400" in err_msg and "key" in err_msg.lower():
            err_msg = "Invalid Gemini API Key. Please verify your API key in the settings."
        return {
            "success": False,
            "error": f"Claim extraction failed: {err_msg}",
            "claims": []
        }
