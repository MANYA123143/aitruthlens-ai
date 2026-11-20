# TruthLens AI – Intelligent PDF Fact-Checking Web Application

TruthLens AI is an AI-powered document verification platform that allows users to upload PDF documents, automatically extract factual claims, verify those claims against live authoritative web data, identify misinformation and outdated statistics, and generate evidence-based audit reports.

---

## 🌟 Key Features

- **High-Fidelity PDF Ingestion:** Page-aware text extraction using `PyMuPDF` with scanned document detection and corrupt file handling.
- **AI-Powered Claim Extraction:** Identifies verifiable numerical statistics, financial figures, dates, and technical assertions using Google Gemini without extracting subjective marketing text.
- **Live Web Grounding Verification:** Cross-references claims against live authoritative web data using Gemini with Google Search Grounding.
- **Transparent 4-Tier Verdict System:**
  - 🟢 **VERIFIED:** Matches reliable external evidence with correct context and values.
  - 🟡 **INACCURATE:** Partially incorrect, materially outdated, or mismatched reporting period.
  - 🔴 **FALSE:** Directly contradicted by authoritative external sources.
  - ⚪ **UNVERIFIABLE:** Insufficient reliable evidence to establish truth value.
- **Interactive SaaS-Style Dashboard:**
  - Status summary metrics & visual distribution charts.
  - Interactive search and multi-status filtering.
  - Expandable evidence cards with clickable source URLs and evidence strength levels.
- **Exportable Reports:**
  - Downloadable structured **CSV** file.
  - Downloadable multi-page audit **PDF Report** with executive summary cards.
- **Session Verification History:** Easily toggle and review previously audited documents.

---

## 🛠️ Technology Stack

- **Language:** Python 3.10+
- **Frontend Framework:** Streamlit
- **AI & Grounding:** Google Gemini API via official `google-genai` SDK
- **Search Grounding:** Google Search Grounding (`types.GoogleSearch()`)
- **PDF Extraction & Generation:** PyMuPDF (`fitz`)
- **Data Processing:** Pandas, Pydantic
- **Deployment Platform:** Streamlit Community Cloud

---

## 📁 Project Structure

```text
truthlens-ai/
│
├── app.py                     # Main Streamlit web application & UI
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation and setup instructions
├── .gitignore                 # Excludes secrets, caches, and temporary files
│
├── modules/
│   ├── __init__.py
│   ├── pdf_extractor.py       # PyMuPDF extraction & page management
│   ├── claim_extractor.py     # Gemini-powered factual claim parser
│   ├── web_verifier.py        # Live Google Search grounding & verification
│   ├── report_generator.py    # CSV and PDF report generation
│   └── utils.py               # Data models, styles, and secret retrieval
│
└── .streamlit/
    └── secrets.toml.example   # Example secrets template
```

---

## 🚀 Local Installation & Execution

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/truthlens-ai.git
cd truthlens-ai
```

### 2. Set Up a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key
Create a `.streamlit/secrets.toml` file from the example:
```bash
# Windows (PowerShell)
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml

# macOS / Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and paste your free Gemini API key:
```toml
GEMINI_API_KEY = "your-actual-gemini-api-key"
```
*(Alternatively, you can enter the API key directly into the application sidebar at runtime).*

### 5. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🌐 Deployment to Streamlit Community Cloud

TruthLens AI is 100% deployment-ready for Streamlit Community Cloud:

1. **Push Code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit of TruthLens AI"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/truthlens-ai.git
   git push -u origin main
   ```
2. **Deploy on Streamlit Cloud:**
   - Log into [share.streamlit.io](https://share.streamlit.io/).
   - Click **New app**.
   - Select your repository (`truthlens-ai`), branch (`main`), and set the main file path to `app.py`.
3. **Configure Secrets on Streamlit Cloud:**
   - In App Settings under **Secrets**, add:
     ```toml
     GEMINI_API_KEY = "AIzaSy..."
     ```
   - Click **Save**. The app will automatically launch with full live web search fact-checking enabled!

---

## 🧪 Testing Scenarios

TruthLens AI has been designed and tested for:
1. **Accurate statistics:** Verifies accurate GDP, company revenues, and population figures.
2. **Fabricated numbers:** Categorizes fabricated facts and impossible dates as `FALSE`.
3. **Outdated information:** Correctly flags historical figures presented as current as `INACCURATE`.
4. **Unverifiable claims:** Safely categorizes internal or unpublicized claims as `UNVERIFIABLE` rather than falsely marking them incorrect.
5. **Corrupted or empty PDFs:** Catches empty files and password protection with clear warnings.

---

## 🛡️ License & Ethical Grounding

TruthLens AI operates under strict factual grounding guidelines: it never invents URLs or statistics and requires external verification before marking claims as verified.
