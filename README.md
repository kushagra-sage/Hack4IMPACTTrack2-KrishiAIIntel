<p align="center">
  <img src="https://img.shields.io/badge/Domain-AI%20%2B%20Agriculture%20%2B%20FinTech-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Stack-FastAPI%20%7C%20YOLO%20%7C%20Qwen2.5--VL%20%7C%20FAISS%20%7C%20Mistral-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

# 🌾 KrishiAIIntel — Tractor Invoice Intelligence System

> **Transforming handwritten and printed tractor invoices into structured financial intelligence — enabling faster loan approvals, smarter portfolio analytics, and data-driven agricultural lending.**

---

## 👥 Team Details

| | Name |
|---|---|
| **Team Name** | **KrishiAIIntel** |
| Member 1 | Kushagra|
| Member 2 | [Amit Behera] |


---

## 🏷️ Domain

**Artificial Intelligence × Agriculture × Financial Intelligence**

---

## 📋 Problem Statement

India's agricultural lending ecosystem processes **millions of tractor invoices annually** — and the vast majority are handled manually. Field officers photograph paper invoices, data-entry operators transcribe them by hand, and loan officers interpret unstructured text to make lending decisions.

**This creates three critical bottlenecks:**

| Pain Point | Impact |
|---|---|
| 🐌 **Manual data entry** | 15–30 minutes per invoice, high error rates, illegible handwriting |
| 🔒 **No structured data** | Invoices exist as images — impossible to aggregate, query, or analyze at scale |
| ⏳ **Slow loan processing** | Days-to-weeks turnaround for loan eligibility decisions that could take seconds |

Rural farmers depend on timely credit to purchase tractors during critical farming seasons. Delays in loan processing directly translate to **missed harvests and lost income**.

---

## 💡 Why This Matters

- ⚡ **Faster Loan Approvals** — Reduce invoice-to-decision time from days to seconds.
- 🌍 **Financial Inclusion** — Extend structured digital lending infrastructure to rural and semi-urban areas.
- 📊 **Portfolio Intelligence** — Enable lenders to aggregate, query, and analyze their entire invoice corpus in real time.
- 🤖 **Automation at Scale** — Replace manual transcription with a fully automated AI pipeline that learns incrementally from every new invoice.

---

## 🧬 Solution Overview

KrishiAIIntel is an **end-to-end AI pipeline** that converts raw invoice images into actionable financial intelligence through a multi-stage processing architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KrishiAIIntel Pipeline                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   📸 Invoice Image                                                  │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────┐                                           │
│   │  YOLO v8 Detection  │──▶ Signature & Stamp localization         │
│   └─────────────────────┘                                           │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────┐                                           │
│   │  Qwen2.5-VL (7B)   │──▶ Structured field extraction            │
│   │  Vision-Language    │    (dealer, model, HP, cost)              │
│   └─────────────────────┘                                           │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────┐                                           │
│   │  Normalization      │──▶ Field validation & standardization     │
│   │  Layer              │    (fuzzy matching, range checks)         │
│   └─────────────────────┘                                           │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────┐           │
│   │  RAG Knowledge Base                                  │           │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │           │
│   │  │  FAISS   │  │  SQLite  │  │  Mistral 7B      │  │           │
│   │  │  Vectors │  │  Agg DB  │  │  Flash LLM       │  │           │
│   │  └──────────┘  └──────────┘  └──────────────────┘  │           │
│   └─────────────────────────────────────────────────────┘           │
│       │                                                             │
│       ▼                                                             │
│   ┌─────────────────────────────────────────────────────┐           │
│   │  Output Layer                                        │           │
│   │  • Structured JSON API responses                     │           │
│   │  • Loan decision support (EMI, eligibility)          │           │
│   │  • Natural-language portfolio chat                   │           │
│   │  • Downloadable HTML reports                         │           │
│   └─────────────────────────────────────────────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔍 **Invoice Field Extraction** | Extracts dealer name, tractor model, horse power, and asset cost from scanned/photographed invoices |
| ✍️ **Signature & Stamp Detection** | YOLO-based object detection with bounding box coordinates for authenticity verification |
| 🧠 **Vision-Language Understanding** | Qwen2.5-VL-7B processes complex, noisy, and handwritten invoice images with chain-of-thought reasoning |
| 🔄 **Real-Time Normalization** | Fuzzy matching and rule-based validation standardize extracted fields against known entities |
| 💬 **RAG-Powered Portfolio Chat** | Ask natural-language questions about your invoice corpus — routed to SQL aggregation or FAISS + LLM retrieval |
| 📊 **Portfolio Analytics Dashboard** | Real-time stats: total invoices, average cost, top models, top dealers, regional distribution |
| 🏦 **Loan Decision Support** | Instant EMI calculations across 5/7/9-year tenures, eligibility classification, and downloadable reports |
| 📥 **Incremental Learning** | Every new invoice processed is automatically ingested into the knowledge base — the system grows smarter with use |
| 🖼️ **Resolution & Enhancement Controls** | Adjust image resolution and apply OpenCV preprocessing before inference for optimal extraction |
| ⚡ **Chain-of-Thought Mode** | Optional "reason" mode activates step-by-step VLM reasoning for complex or ambiguous invoices |

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             FRONTEND (React + Vite)                      │
│                                                                          │
│   ┌──────────────┐   ┌──────────────────┐   ┌────────────────────────┐  │
│   │ Invoice       │   │ Portfolio         │   │ Loan Decision          │  │
│   │ Analysis Tab  │   │ Intelligence Tab  │   │ Support Cards          │  │
│   │              │   │                  │   │                        │  │
│   │ • Upload     │   │ • Stats Dashboard│   │ • EMI Calculator       │  │
│   │ • Preview    │   │ • Chat Interface │   │ • Eligibility Status   │  │
│   │ • Results    │   │ • Example Queries│   │ • Report Download      │  │
│   └──────┬───────┘   └────────┬─────────┘   └───────────┬────────────┘  │
│          │                    │                          │                │
└──────────┼────────────────────┼──────────────────────────┼────────────────┘
           │                    │                          │
           ▼                    ▼                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI BACKEND                                 │
│                                                                          │
│   /extract ─────────┐                                                    │
│   /process-invoice ─┤                                                    │
│   /extract_batch ───┤  ┌────────────────────────────────────────────┐    │
│                     ├─▶│  Inference Engine                          │    │
│                     │  │  YOLO → Qwen2.5-VL → Normalization        │    │
│                     │  └───────────────┬────────────────────────────┘    │
│                     │                  │                                  │
│                     │                  ▼  (auto-ingest)                   │
│   /chat ────────────┤  ┌────────────────────────────────────────────┐    │
│   /portfolio/stats ─┤─▶│  RAG Engine                               │    │
│                     │  │  FAISS + SQLite + Mistral 7B (HF API)     │    │
│                     │  └────────────────────────────────────────────┘    │
│   /decision-support ┤  ┌────────────────────────────────────────────┐    │
│                     ├─▶│  Decision Engine                          │    │
│   /generate-report ─┘  │  EMI calc + Eligibility + Report gen      │    │
│                        └────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 End-to-End Flow

Here is exactly what happens when a user interacts with KrishiAIIntel:

### Step 1 — Upload Invoice
The user uploads one or more invoice images (JPG, PNG, or PDF). PDFs are automatically split into page images. A resolution slider lets the user optimize image quality before processing.

### Step 2 — AI-Powered Extraction
The backend runs a two-stage inference pipeline:
1. **YOLO v8** scans the image for signature and stamp regions, returning bounding box coordinates.
2. **Qwen2.5-VL-7B** (4-bit quantized) reads the full document and extracts structured fields: dealer name, tractor model, horse power, and asset cost.

An optional **chain-of-thought reasoning mode** enables the VLM to show its step-by-step interpretation for ambiguous or noisy documents.

### Step 3 — Normalize & Validate
Extracted fields pass through a normalization layer that:
- Fuzzy-matches dealer/model names against known entities (using RapidFuzz)
- Validates numeric fields against expected ranges (HP: 20–120, Cost: ₹1L–₹30L)
- Standardizes formatting for downstream consistency

### Step 4 — Ingest into Knowledge Base
The processed invoice is **automatically ingested** into the RAG knowledge base:
- A text embedding (via `all-MiniLM-L6-v2`) is added to the **FAISS** vector index
- Structured fields are inserted/updated in the **in-memory SQLite** database
- The JSON persistence layer is updated for durability

Duplicate `doc_id` entries are detected and updated in-place — the FAISS index is rebuilt to prevent stale vectors.

### Step 5 — Query & Analyze
Users switch to the **Portfolio Intelligence** tab to:
- View **real-time dashboard** stats (total invoices, average cost, top models, regional distribution)
- Ask **natural-language questions** via the chat interface (e.g., _"What is the average cost of Mahindra tractors?"_)
- The query router intelligently selects between **SQL aggregation** (for COUNT/AVG/SUM queries) and **FAISS retrieval + LLM generation** (for semantic questions)

### Step 6 — Loan Decision Support
For each processed invoice, the system calculates:
- **EMI options** across 5, 7, and 9-year tenures at 10.5% annual interest
- **Eligibility classification**: High / Moderate / Review Required
- **Downloadable HTML report** with all extracted data and recommendations

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Framework** | FastAPI | Async REST API with auto-generated OpenAPI docs |
| **Object Detection** | YOLOv8 (custom trained) | Signature & stamp localization on invoice images |
| **Vision-Language Model** | Qwen2.5-VL-7B-Instruct | Structured text extraction from document images |
| **Quantization** | BitsAndBytes (NF4, 4-bit) | Reduces VRAM from ~28GB to ~8GB without quality loss |
| **Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) | Convert invoice text to dense vectors for retrieval |
| **Vector Store** | FAISS (IndexFlatIP) | Cosine-similarity search over invoice embeddings |
| **Aggregation DB** | SQLite (in-memory) | SQL-based portfolio analytics (COUNT, AVG, SUM) |
| **LLM Generation** | Mistral-7B-Instruct (HuggingFace API) | Grounded answer generation from retrieved context + offline fallback |
| **Normalization** | RapidFuzz + rule engine | Fuzzy matching and field validation |
| **Image Processing** | OpenCV + Pillow | Optional enhancement preprocessing |
| **Frontend** | React 18 + Vite | Modern SPA with tab-based navigation |
| **UI Framework** | Tailwind CSS + Framer Motion | Dark themed UI with glassmorphism and animations |
| **3D Visuals** | Three.js / React Three Fiber | Ambient 3D particle background |
| **Deployment** | Docker + HuggingFace Spaces | Containerized deployment with GPU support |

---

## 🚀 How to Run

### Prerequisites
- Python 3.10+
- CUDA-capable GPU with ≥10 GB VRAM
- Node.js 18+
- HuggingFace API token (for LLM generation — system works offline via fallback)

### Backend

```bash
# Clone the repository
git clone https://github.com/your-org/KrishiAIIntel.git
cd KrishiAIIntel

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variable for HuggingFace LLM (optional — fallback works without it)
export HF_TOKEN="your-huggingface-token"

# (Optional) Pre-build the RAG database from existing invoices
python build_rag_db.py

# Start the API server
python app.py
```

The backend starts at **`http://localhost:7860`** with interactive docs at `/docs`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

> **Note:** No `.env` file is needed for local development. The Vite dev server proxy (`vite.config.js`) automatically forwards all API calls to `http://localhost:7860`. For production builds pointing at a remote backend, set the environment variable at build time:
> ```bash
> VITE_API_BASE=https://your-backend-url npm run build
> ```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check and model loading status |
| `POST` | `/extract` | Extract structured fields from a single invoice image |
| `POST` | `/process-invoice` | Process invoice with simplified response format for frontend |
| `POST` | `/extract_batch` | Batch extraction from multiple invoice images |
| `POST` | `/decision-support` | Generate EMI options, eligibility, and loan recommendations |
| `POST` | `/chat` | Natural-language query against the invoice knowledge base |
| `GET` | `/portfolio/stats` | Portfolio summary statistics for the dashboard |
| `POST` | `/generate-report` | Generate a downloadable HTML analysis report |

---

## 📦 Sample Output

### Invoice Extraction (`POST /extract`)

```json
{
  "doc_id": "MAHINDRA_575_DI_001",
  "fields": {
    "dealer_name": "Rajesh Agri Tractors Pvt Ltd",
    "model_name": "Mahindra 575 DI",
    "horse_power": 50,
    "asset_cost": 625000,
    "signature": {
      "present": true,
      "bbox": [142, 387, 298, 442]
    },
    "stamp": {
      "present": true,
      "bbox": [405, 391, 512, 478]
    }
  },
  "confidence": 0.91,
  "processing_time_sec": 4.2,
  "cost_estimate_usd": 0.00058
}
```

### Chat Query (`POST /chat`)

```json
// Request
{ "query": "What is the average asset cost across all invoices?" }

// Response
{
  "answer": "The average asset cost across all invoices is ₹6,42,375.50.",
  "sources": [],
  "query_type": "sql",
  "intent": "average_cost"
}
```

### Decision Support (`POST /decision-support`)

```json
{
  "decision_support": {
    "emi_options": {
      "5_years": 13456.78,
      "7_years": 10234.56,
      "9_years": 8765.43
    },
    "recommended_plan": "7_years",
    "eligibility": "High Eligibility",
    "reason": "Asset cost ₹6,25,000 is within the ₹10L threshold and horse power (50 HP) meets the ≥50 HP requirement.",
    "annual_interest_rate": 10.5
  }
}
```

---

## ⚡ Performance

| Metric | Value |
|---|---|
| **Per-invoice processing time** | ~4–8 seconds (GPU-dependent) |
| **YOLO detection latency** | <500ms |
| **VLM extraction latency** | 3–7 seconds |
| **RAG query response** | <2 seconds (SQL path: <100ms) |
| **VRAM footprint** | ~8 GB (4-bit quantized Qwen2.5-VL) |
| **Cost per invoice** | ~$0.002 (GPU compute time) |
| **Concurrent request support** | Thread-safe RAG ingestion with locking |

---

## 📂 Project Structure

```
KrishiAIIntel/
├── app.py                    # FastAPI server — all endpoints
├── config.py                 # Model paths, thresholds, API metadata
├── model_manager.py          # YOLO + Qwen2.5-VL loading and lifecycle
├── inference.py              # Two-stage processing pipeline + validation
├── decision.py               # EMI calculator + eligibility classifier
├── rag_engine.py             # FAISS + SQLite + HuggingFace RAG engine
├── report_generator.py       # HTML report generation
├── build_rag_db.py           # Offline script to pre-populate RAG DB
├── generate_invoice_db.py    # Dataset processing utility
├── requirements.txt          # Python dependencies
├── Dockerfile                # Containerized deployment
├── utils/
│   ├── normalization.py      # Fuzzy matching + field validation
│   └── models/
│       └── best.pt           # Custom-trained YOLO model weights
├── data/
│   └── invoices_db.json      # Persisted invoice knowledge base
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── App.jsx                       # Main app with tab navigation
        ├── main.jsx                      # React entry point
        ├── index.css                     # Global styles + animations
        ├── utils/
        │   ├── api.js                    # Centralized API client
        │   └── fileConverter.js          # PDF → image conversion
        └── components/
            ├── FileUpload.jsx            # Drag-and-drop uploader
            ├── ImagePreview.jsx          # Resolution slider + enhancement toggle
            ├── ProgressIndicator.jsx     # Processing progress bar
            ├── ResultCard.jsx            # Extraction results display
            ├── LoanSummaryCard.jsx       # EMI + eligibility card
            ├── PortfolioChat.jsx         # RAG chat interface
            ├── PortfolioStats.jsx        # Analytics dashboard
            ├── AIPipelineVisualization.jsx# Pipeline flow visualization
            └── Scene3D.jsx               # Ambient 3D background
```

---

## 🔮 Future Scope

- **Regional & Date Intelligence** — Extract invoice dates and geographic regions with dedicated OCR sub-models for improved temporal and spatial analytics.
- **Credit Scoring Engine** — Build a composite creditworthiness score by correlating extracted invoice data with historical repayment patterns and external credit bureau data.
- **Executive Dashboard** — Admin-facing dashboard with trend analysis, anomaly detection, portfolio risk heatmaps, and automated reporting pipelines.
- **Multilingual Expansion** — Extend VLM prompts and normalization rules to support Hindi, Tamil, Telugu, and other regional Indian language invoices.
- **Mobile Capture SDK** — Lightweight on-device preprocessing library for field officers to capture and submit invoices directly from smartphones.
- **Audit Trail & Compliance** — Full extraction history with version tracking, manual override logging, and regulatory compliance reporting.

---

## 📄 License

This project is licensed under the **MIT License**.

---

<p align="center">
  <b>Built with 🌾 by Team KrishiAIIntel</b><br/>
  <sub>AI-Powered Agricultural Finance Intelligence</sub>
</p>