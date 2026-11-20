"""
Live Web Fact Verification Module using Gemini Google Search Grounding.
Cross-references claims against live authoritative web data,
extracts real sources with URLs, validates numerical statistics,
and classifies into VERIFIED, INACCURATE, FALSE, or UNVERIFIABLE.
"""

import json
import re
import time
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from modules.utils import VerificationResult, SourceEvidence


VERIFICATION_SYSTEM_PROMPT = """You are TruthLens AI, a world-class factual verification analyst.
Your objective is to independently verify factual claims using live search results.

CRITICAL RULES:
1. Search the web for authoritative sources: government portals (.gov, .org, official statistics agencies), academic publications, corporate reports, reputable financial media (Reuters, Bloomberg, FT, WSJ), and trusted global outlets.
2. Cross-reference the claim's specific dates, numerical values, currency, percentages, units, and geographical contexts.
3. Compare the original figure with the retrieved live facts.
4. Detect outdated information vs fabricated statistics.
5. NEVER invent or hallucinate sources, titles, or URLs. Only refer to actual information discovered.
6. If no reliable evidence confirms or denies the statement, you MUST classify it as UNVERIFIABLE. Lack of search results alone does NOT make a claim FALSE.

You MUST classify the claim into exactly one of these 4 categories:
- VERIFIED: The claim matches reliable external evidence, including the relevant date, context, and numerical value.
- INACCURATE: The claim is partially incorrect, materially outdated, uses an incorrect figure, or has a mismatch in reporting period or context.
- FALSE: Reliable evidence directly contradicts the claim, or authoritative sources prove the stated fact is fabricated or incorrect.
- UNVERIFIABLE: There is insufficient reliable evidence to establish whether the claim is true or false.

Return a valid JSON object matching this schema:
{
  "verification_status": "VERIFIED / INACCURATE / FALSE / UNVERIFIABLE",
  "explanation": "Clear, objective explanation of why this verdict was reached.",
  "corrected_info": "Accurate, up-to-date figure or context if inaccurate/false, or null if verified or unverifiable",
  "evidence_text": "Key facts retrieved from live search supporting this conclusion",
  "evidence_strength": "High / Medium / Low"
}

Return ONLY raw JSON. No markdown fences.
"""


def verify_single_claim(
    client: genai.Client,
    claim: Dict[str, Any],
    model_name: str = "gemini-2.5-flash"
) -> VerificationResult:
    """
    Verifies a single claim using Google Search Grounding with Gemini.
    Extracts real grounding metadata and grounding chunks (URLs, titles).
    """
    claim_id = claim.get("claim_id", 1)
    claim_text = claim.get("claim_text", "")
    claim_type = claim.get("claim_type", "Statistic")
    page_number = claim.get("page_number", 1)
    ref_year = claim.get("reference_year")
    num_val = claim.get("numerical_value")
    unit = claim.get("unit")

    context_str = f"Claim: \"{claim_text}\"\n"
    if num_val:
        context_str += f"Target Numerical Value: {num_val} {unit or ''}\n"
    if ref_year:
        context_str += f"Context / Year: {ref_year}\n"

    user_prompt = f"""Investigate and fact-check this claim using Google Search:
{context_str}

Perform a live web search to verify the factual accuracy of this statement.
Compare numerical figures, timelines, and facts against authoritative sources.
Classify strictly as VERIFIED, INACCURATE, FALSE, or UNVERIFIABLE.
Respond with the specified JSON format."""

    try:
        # Enable Google Search grounding tool
        config = types.GenerateContentConfig(
            temperature=0.0,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            system_instruction=VERIFICATION_SYSTEM_PROMPT
        )

        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=config
        )

        # Extract Grounding Metadata (Real sources with titles and URLs)
        extracted_sources: List[SourceEvidence] = []
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            grounding_meta = getattr(candidate, "grounding_metadata", None)
            
            if grounding_meta:
                # 1. Grounding chunks
                chunks = getattr(grounding_meta, "grounding_chunks", []) or []
                for chunk in chunks:
                    web = getattr(chunk, "web", None)
                    if web:
                        uri = getattr(web, "uri", "")
                        title = getattr(web, "title", "Web Reference")
                        if uri and not any(s.url == uri for s in extracted_sources):
                            extracted_sources.append(SourceEvidence(
                                title=title or "Verified Web Source",
                                url=uri,
                                snippet=None
                            ))
                
                # 2. Search entry point or web search queries
                web_queries = getattr(grounding_meta, "web_search_queries", []) or []

        # Parse text response
        raw_text = response.text or "{}"
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        # Extract JSON using regex if surrounded by text
        try:
            parsed = json.loads(clean_text)
        except Exception:
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
            else:
                parsed = {
                    "verification_status": "UNVERIFIABLE",
                    "explanation": f"Unable to parse structured verification response: {clean_text[:200]}",
                    "evidence_strength": "Low"
                }

        status = parsed.get("verification_status", "UNVERIFIABLE").upper().strip()
        if status not in ["VERIFIED", "INACCURATE", "FALSE", "UNVERIFIABLE"]:
            # Fallback normalization
            if "VERIF" in status:
                status = "VERIFIED"
            elif "INACC" in status:
                status = "INACCURATE"
            elif "FALSE" in status:
                status = "FALSE"
            else:
                status = "UNVERIFIABLE"

        return VerificationResult(
            claim_id=claim_id,
            claim_text=claim_text,
            claim_type=claim_type,
            page_number=page_number,
            verification_status=status,
            explanation=parsed.get("explanation", "Verification completed with available search evidence."),
            corrected_info=parsed.get("corrected_info"),
            evidence_text=parsed.get("evidence_text"),
            evidence_strength=parsed.get("evidence_strength", "Medium" if extracted_sources else "Low"),
            sources=extracted_sources
        )

    except Exception as e:
        err_msg = str(e)
        status = "UNVERIFIABLE"
        expl = f"Fact check could not be completed due to service error: {err_msg}"
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            expl = "Gemini API rate limit or search quota exceeded. Please wait a moment and retry."

        return VerificationResult(
            claim_id=claim_id,
            claim_text=claim_text,
            claim_type=claim_type,
            page_number=page_number,
            verification_status=status,
            explanation=expl,
            corrected_info=None,
            evidence_text="Verification paused due to connection/quota issue.",
            evidence_strength="Low",
            sources=[]
        )


def verify_claims_batch(
    claims: List[Dict[str, Any]],
    api_key: str,
    model_name: str = "gemini-2.5-flash",
    progress_callback=None
) -> List[Dict[str, Any]]:
    """
    Verifies a list of claims sequentially with rate limit pacing
    and progress reporting.
    """
    if not api_key:
        raise ValueError("Missing Gemini API Key.")

    client = genai.Client(
        api_key=api_key,
        http_options={"api_version": "v1beta"}
    )
    results = []
    total = len(claims)

    for i, claim in enumerate(claims):
        if progress_callback:
            progress_callback(i, total, claim.get("claim_text", "")[:60])
        
        result = verify_single_claim(client, claim, model_name=model_name)
        results.append(result.model_dump())
        
        # Pacing to protect free-tier rate limits (15 RPM safe interval)
        if i < total - 1:
            time.sleep(1.0)

    if progress_callback:
        progress_callback(total, total, "Verification complete!")

    return results
