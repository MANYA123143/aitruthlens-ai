"""
TruthLens AI – Intelligent PDF Fact-Checking Web Application
Main Streamlit Application Dashboard
"""

import streamlit as st
import pandas as pd
import datetime
from modules.pdf_extractor import extract_text_from_pdf
from modules.claim_extractor import extract_claims_from_text
from modules.web_verifier import verify_claims_batch
from modules.report_generator import generate_csv_report, generate_pdf_report
from modules.utils import get_gemini_api_key, get_status_badge, get_status_color

# Page Configuration
st.set_page_config(
    page_title="TruthLens AI – Intelligent Document Fact-Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling: Modern SaaS Dark Navy & Blue Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Gradient Header */
    .main-header {
        background: linear-gradient(135deg, #090d16 0%, #0f172a 50%, #1e293b 100%);
        padding: 2.2rem 2.4rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 2rem;
        border-left: 6px solid #3b82f6;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25), 0 8px 10px -6px rgba(15, 23, 42, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::after {
        content: "";
        position: absolute;
        top: -40%;
        right: -10%;
        width: 320px;
        height: 320px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(15, 23, 42, 0) 70%);
        pointer-events: none;
    }

    .main-header h1 {
        color: #ffffff !important;
        font-weight: 800;
        font-size: 2.3rem;
        margin-bottom: 0.35rem;
        letter-spacing: -0.03em;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .main-header p {
        color: #94a3b8 !important;
        font-size: 1.05rem;
        margin-bottom: 0;
        font-weight: 400;
        max-width: 800px;
        line-height: 1.5;
    }

    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.3rem 1.1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03), 0 1px 2px rgba(0,0,0,0.02);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.06);
        border-color: #cbd5e1;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
    }
    .metric-card .num {
        font-size: 2.3rem;
        font-weight: 800;
        margin: 0.35rem 0 0.15rem 0;
        line-height: 1;
        letter-spacing: -0.03em;
    }

    /* Sidebar Logo & Branding */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.2rem 0 1.2rem 0;
    }
    .brand-icon {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35);
    }
    .brand-title {
        font-weight: 800;
        font-size: 1.35rem;
        color: #0f172a;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }
    .brand-subtitle {
        font-size: 0.75rem;
        font-weight: 500;
        color: #64748b;
    }

    /* Accuracy Callout Banner */
    .accuracy-callout {
        background: linear-gradient(90deg, #eff6ff 0%, #f8fafc 100%);
        border: 1px solid #bfdbfe;
        border-left: 5px solid #2563eb;
        border-radius: 10px;
        padding: 1rem 1.4rem;
        margin-bottom: 1.5rem;
        color: #1e3a8a;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        transition: all 0.15s ease-in-out;
    }
    .stButton>button:hover {
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    /* Evidence source link pills */
    .source-link-pill {
        display: inline-flex;
        align-items: center;
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 6px 12px;
        border-radius: 8px;
        color: #1d4ed8;
        font-size: 0.82rem;
        text-decoration: none;
        margin: 4px 6px 4px 0;
        font-weight: 500;
        transition: all 0.15s ease;
    }
    .source-link-pill:hover {
        background: #eff6ff;
        border-color: #93c5fd;
        color: #1e40af;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "verification_history" not in st.session_state:
    st.session_state["verification_history"] = []

if "current_results" not in st.session_state:
    st.session_state["current_results"] = None

if "extracted_claims" not in st.session_state:
    st.session_state["extracted_claims"] = None

if "pdf_data" not in st.session_state:
    st.session_state["pdf_data"] = None

if "current_filename" not in st.session_state:
    st.session_state["current_filename"] = ""


# Sidebar Configuration & Navigation
with st.sidebar:
    st.markdown("""
    <div class="brand-container">
        <div class="brand-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="m9 12 2 2 4-4"/>
            </svg>
        </div>
        <div>
            <div class="brand-title">TruthLens AI</div>
            <div class="brand-subtitle">Document Verification</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    nav_selection = st.radio(
        "Navigation",
        ["Dashboard", "Fact Check a PDF", "Verification History", "About the Application"],
        index=1 if st.session_state["current_results"] is None else 0
    )

    st.markdown("---")
    st.subheader("⚙️ Settings & API")

    configured_key = get_gemini_api_key()
    user_api_key = st.text_input(
        "Google Gemini API Key",
        value=configured_key if configured_key else "",
        type="password",
        help="Free API key from Google AI Studio (https://aistudio.google.com/)"
    )

    selected_model = st.selectbox(
        "Gemini Model",
        ["gemini-2.5-flash", "gemini-1.5-flash"],
        index=0,
        help="Gemini 2.5 Flash supports free-tier Google Search grounding."
    )

    max_claims_to_check = st.slider(
        "Max Claims to Verify",
        min_value=3,
        max_value=20,
        value=8,
        step=1,
        help="Controlled limit protects free API rate-limits while ensuring thorough verification."
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.8rem; color:#64748b;'>TruthLens AI v1.0.0<br/>Powered by Google Gemini 2.5 & Google Search Grounding</div>",
        unsafe_allow_html=True
    )


# Effective API key
active_api_key = user_api_key.strip() if user_api_key else configured_key


# Top Header
st.markdown("""
<div class="main-header">
    <h1>TruthLens AI</h1>
    <p>Detect misleading statistics, outdated information, and inaccurate claims using AI-powered fact verification.</p>
</div>
""", unsafe_allow_html=True)


# --- VIEW 1: FACT CHECK A PDF ---
if nav_selection == "Fact Check a PDF":
    st.subheader("📄 Upload & Verify PDF Document")
    st.write("Upload any PDF report, research paper, earnings summary, or press release to audit factual claims.")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        accept_multiple_files=False,
        help="Upload standard PDF documents up to 25 MB."
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_size_kb = len(file_bytes) / 1024
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📁 **Selected Document:** `{uploaded_file.name}` ({file_size_kb:.1f} KB)")
        with col2:
            if st.button("Clear / Reset", type="secondary", use_container_width=True):
                st.session_state["pdf_data"] = None
                st.session_state["extracted_claims"] = None
                st.session_state["current_results"] = None
                st.rerun()

        # Step 1: Extract Text preview
        if st.session_state["pdf_data"] is None or st.session_state["current_filename"] != uploaded_file.name:
            with st.spinner("Extracting text and page boundaries using PyMuPDF..."):
                pdf_info = extract_text_from_pdf(file_bytes, uploaded_file.name)
                st.session_state["pdf_data"] = pdf_info
                st.session_state["current_filename"] = uploaded_file.name
                st.session_state["extracted_claims"] = None
                st.session_state["current_results"] = None

        pdf_info = st.session_state["pdf_data"]

        if not pdf_info["success"]:
            st.error(f"❌ {pdf_info['error']}")
        else:
            if pdf_info.get("is_scanned"):
                st.warning("⚠️ **Low text density detected:** This document may be a scanned or image-based PDF. Digital text is minimal. For best results, use digital PDFs or OCR.")

            # Document preview accordion
            with st.expander(f"📑 Preview Extracted Text ({pdf_info['total_pages']} pages, {pdf_info['total_chars']} characters)", expanded=False):
                st.text_area("Document Content", value=pdf_info["full_text"][:3000] + ("\n...[Preview truncated]" if len(pdf_info["full_text"]) > 3000 else ""), height=220)

            # Analyze Document Button
            st.markdown("---")
            if not active_api_key:
                st.warning("🔑 **Gemini API Key Required:** Please enter your Google Gemini API key in the left sidebar to start AI-powered fact verification.")
            else:
                analyze_clicked = st.button("🚀 Analyze & Fact Check Document", type="primary", use_container_width=True)

                if analyze_clicked:
                    # Pipeline Stage 1: Claim Extraction
                    with st.status("🔍 Step 1: Extracting factual claims with Gemini...", expanded=True) as status_box:
                        claim_res = extract_claims_from_text(
                            pages_data=pdf_info["pages"],
                            api_key=active_api_key,
                            model_name=selected_model,
                            max_claims=max_claims_to_check
                        )

                        if not claim_res["success"]:
                            status_box.update(label="Claim extraction failed", state="error")
                            st.error(claim_res["error"])
                            st.stop()

                        claims = claim_res["claims"]
                        st.session_state["extracted_claims"] = claims
                        status_box.write(f"✅ Extracted **{len(claims)} verifiable claims** (numbers, metrics, dates, and financial figures).")

                        # Pipeline Stage 2: Web Fact Verification
                        status_box.update(label="🌐 Step 2: Cross-referencing claims against live web sources...", state="running")
                        
                        progress_bar = st.progress(0.0)
                        status_text = st.empty()

                        def update_progress(curr, tot, claim_snippet):
                            pct = curr / tot if tot > 0 else 1.0
                            progress_bar.progress(pct)
                            status_text.caption(f"Verifying ({curr}/{tot}): *{claim_snippet}*")

                        try:
                            verification_results = verify_claims_batch(
                                claims=claims,
                                api_key=active_api_key,
                                model_name=selected_model,
                                progress_callback=update_progress
                            )
                        except Exception as e:
                            status_box.update(label="Verification failed", state="error")
                            st.error(f"Verification error: {str(e)}")
                            st.stop()

                        status_box.update(label="🎉 Verification complete!", state="complete")

                    # Save to state and history
                    st.session_state["current_results"] = verification_results
                    analysis_record = {
                        "filename": uploaded_file.name,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "total_claims": len(verification_results),
                        "results": verification_results
                    }
                    st.session_state["verification_history"].append(analysis_record)

                    st.success("✅ Audit complete! Directing to the Results Dashboard...")
                    st.balloons()
                    st.rerun()

    # If results already exist for current file, prompt to view dashboard
    if st.session_state.get("current_results"):
        st.markdown("---")
        st.info("💡 You have active fact-checking results available. Switch to the **Dashboard** view to view the interactive breakdown and download audit reports.")


# --- VIEW 2: RESULTS DASHBOARD ---
elif nav_selection == "Dashboard":
    results = st.session_state.get("current_results")

    if not results:
        st.info("ℹ️ No active document analysis found. Please navigate to **'Fact Check a PDF'** in the sidebar to upload and audit a document.")
    else:
        doc_name = st.session_state.get("current_filename", "Uploaded Document")
        st.subheader(f"📊 Verification Report: {doc_name}")

        # Metrics computation
        total_c = len(results)
        v_count = sum(1 for r in results if r.get("verification_status") == "VERIFIED")
        i_count = sum(1 for r in results if r.get("verification_status") == "INACCURATE")
        f_count = sum(1 for r in results if r.get("verification_status") == "FALSE")
        u_count = sum(1 for r in results if r.get("verification_status") == "UNVERIFIABLE")
        
        # Transparent document accuracy calculation
        accuracy_prop = (v_count / total_c * 100) if total_c > 0 else 0

        # Top Metric Cards
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        with m_col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Claims</h3>
                <div class="num" style="color:#0f172a;">{total_c}</div>
                <span style="font-size:0.75rem; color:#64748b;">Audited from PDF</span>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Verified</h3>
                <div class="num" style="color:#10b981;">{v_count}</div>
                <span style="font-size:0.75rem; color:#10b981;">Supported by Web</span>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Inaccurate</h3>
                <div class="num" style="color:#f59e0b;">{i_count}</div>
                <span style="font-size:0.75rem; color:#f59e0b;">Outdated / Off</span>
            </div>
            """, unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>False</h3>
                <div class="num" style="color:#ef4444;">{f_count}</div>
                <span style="font-size:0.75rem; color:#ef4444;">Directly Contradicted</span>
            </div>
            """, unsafe_allow_html=True)
        with m_col5:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Unverifiable</h3>
                <div class="num" style="color:#6b7280;">{u_count}</div>
                <span style="font-size:0.75rem; color:#6b7280;">Insufficient Sources</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Accuracy Disclaimer Banner
        st.markdown(f"""
        <div class="accuracy-callout">
            <div style="font-weight:700; font-size:1.05rem; margin-bottom:0.25rem;">
                📌 Document Accuracy Proportion: {accuracy_prop:.1f}%
            </div>
            <div style="font-size:0.88rem; color:#334155;">
                {v_count} verified out of {total_c} extracted claims. <em>Note: This metric reflects the empirical proportion of claims directly verified against live web search results, not an independent legal certification.</em>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Visual Chart & Filter Controls
        chart_col, filter_col = st.columns([1, 1])

        with chart_col:
            st.markdown("##### 📈 Claim Distribution")
            chart_df = pd.DataFrame({
                "Status": ["VERIFIED", "INACCURATE", "FALSE", "UNVERIFIABLE"],
                "Count": [v_count, i_count, f_count, u_count]
            })
            st.bar_chart(chart_df.set_index("Status"), color="#2563eb", height=240)

        with filter_col:
            st.markdown("##### 🔍 Filter Claims")
            status_filter = st.multiselect(
                "Filter by Verification Status",
                ["VERIFIED", "INACCURATE", "FALSE", "UNVERIFIABLE"],
                default=["VERIFIED", "INACCURATE", "FALSE", "UNVERIFIABLE"]
            )
            search_query = st.text_input("Search Claim Text or Keywords", placeholder="Type keywords (e.g. revenue, 2024, GDP)...")

        # Download Section
        st.markdown("---")
        st.subheader("📥 Export Fact-Checking Reports")
        d_col1, d_col2 = st.columns(2)

        with d_col1:
            csv_data = generate_csv_report(results, doc_name)
            st.download_button(
                label="📄 Download CSV Report",
                data=csv_data,
                file_name=f"truthlens_factcheck_{doc_name}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with d_col2:
            try:
                pdf_report_bytes = generate_pdf_report(results, doc_name)
                st.download_button(
                    label="📑 Download Full PDF Fact-Check Report",
                    data=pdf_report_bytes,
                    file_name=f"truthlens_audit_report_{doc_name}",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Could not prepare PDF download: {e}")

        # Claim-by-Claim Detailed Evidence Section
        st.markdown("---")
        st.subheader("🔎 Detailed Claim-by-Claim Evidence")

        # Apply filtering
        filtered_results = [
            r for r in results
            if r.get("verification_status") in status_filter
            and (not search_query or search_query.lower() in r.get("claim_text", "").lower() or search_query.lower() in r.get("explanation", "").lower())
        ]

        if not filtered_results:
            st.warning("No claims match the active filter or search criteria.")
        else:
            for item in filtered_results:
                cid = item.get("claim_id")
                status = item.get("verification_status", "UNVERIFIABLE")
                pnum = item.get("page_number", 1)
                ctype = item.get("claim_type", "Statistic")
                badge_html = get_status_badge(status)
                border_col = get_status_color(status)

                with st.container():
                    st.markdown(f"""
                    <div style="border-left: 5px solid {border_col}; padding: 1rem 1.2rem; background: #ffffff; border-radius: 6px; margin-bottom: 0.8rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem;">
                            <span style="font-size:0.82rem; font-weight:600; color:#64748b;">CLAIM #{cid} &bull; PDF PAGE {pnum} &bull; TYPE: {ctype.upper()}</span>
                            <span>{badge_html}</span>
                        </div>
                        <div style="font-size:1.05rem; font-weight:600; color:#1e293b; margin-bottom:0.4rem;">
                            &ldquo;{item.get('claim_text')}&rdquo;
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander(f"🔎 View Evidence & Live Sources (Claim #{cid})", expanded=False):
                        st.markdown(f"**Analysis Verdict:** {item.get('explanation')}")

                        if item.get("corrected_info") and str(item.get("corrected_info")).strip() and str(item.get("corrected_info")).strip().lower() != "none":
                            st.markdown(f"**💡 Verified / Corrected Context:** `{item.get('corrected_info')}`")

                        if item.get("evidence_text"):
                            st.markdown(f"**Key Live Evidence:** {item.get('evidence_text')}")

                        st.markdown(f"**Evidence Reliability Strength:** `{item.get('evidence_strength', 'Medium')}`")

                        # Clickable Sources
                        sources = item.get("sources", [])
                        if sources:
                            st.markdown("**Authoritative Live Web Sources:**")
                            for s in sources:
                                s_url = s.get("url", "")
                                s_title = s.get("title") or s_url
                                if s_url:
                                    st.markdown(f'<a href="{s_url}" target="_blank" class="source-link-pill">🔗 {s_title}</a>', unsafe_allow_html=True)
                        else:
                            st.caption("No specific live URL returned for this claim. Classified based on lack of verifiable external documentation.")


# --- VIEW 3: VERIFICATION HISTORY ---
elif nav_selection == "Verification History":
    st.subheader("🕒 Session Verification History")
    history = st.session_state.get("verification_history", [])

    if not history:
        st.info("No documents have been audited during this session yet. Upload a PDF to start auditing.")
    else:
        st.write(f"Audited documents in current session: **{len(history)}**")
        for idx, rec in enumerate(reversed(history)):
            with st.expander(f"📄 {rec['filename']} — {rec['date']} ({rec['total_claims']} claims audited)"):
                st.write(f"Analyzed on: **{rec['date']}**")
                st.write(f"Total Claims Analyzed: **{rec['total_claims']}**")
                
                if st.button(f"Load into Dashboard #{idx+1}", key=f"load_hist_{idx}"):
                    st.session_state["current_results"] = rec["results"]
                    st.session_state["current_filename"] = rec["filename"]
                    st.rerun()


# --- VIEW 4: ABOUT THE APPLICATION ---
elif nav_selection == "About the Application":
    st.subheader("ℹ️ About TruthLens AI")
    st.markdown("""
    **TruthLens AI** is an intelligent, automated PDF fact-checking and document verification platform.

    ### 🛡️ Why TruthLens AI?
    Modern reports, financial prospectuses, press releases, and articles are filled with unverified numbers, outdated market forecasts, and manipulated statistics. TruthLens AI automates the investigative audit process:
    
    1. **PDF Parsing:** Extracts text across pages while retaining original page index references.
    2. **Factual Claim Extraction:** Gemini AI extracts verifiable claims (numerical statistics, revenue, dates, scientific facts) while filtering out subjective marketing prose.
    3. **Live Web Grounding:** Uses Google Search grounding via Gemini to cross-reference statements with live, authoritative web sources (government statistics, SEC filings, recognized media, and academic databases).
    4. **4-Tier Classification Matrix:**
       - **VERIFIED:** Corroborated with high-confidence live evidence.
       - **INACCURATE:** Outdated statistics, mismatched reporting years, or rounding discrepancies.
       - **FALSE:** Refuted or contradicted by authoritative sources.
       - **UNVERIFIABLE:** Insufficient external proof to confirm or refute.
    5. **Exportable Audit Reports:** Generates structured CSV records and downloadable PDF audit reports.

    ### 🔒 Security & Privacy
    - Uploaded files are processed in-memory and are never stored permanently.
    - API keys are secured via Streamlit Secrets and never exposed in version control.
    - Complies with free-tier usage parameters with gentle pacing and configurable limits.
    """)
