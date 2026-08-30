# ThreatIQ — AI RAG Security Threat Prioritizer Pro

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.x-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Gemini](https://img.shields.io/badge/Google_Gemini-3.6_Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **ThreatIQ** is an AI-powered security alert triage and incident prioritization platform that fuses machine learning anomaly detection, asset criticality weighting, MITRE ATT&CK correlation, and Retrieval-Augmented Generation (RAG) to turn overwhelming alert noise into prioritized, explainable, evidence-backed incident response actions.

---

## Key Highlights & Architecture

ThreatIQ eliminates alert fatigue for Security Operations Center (SOC) analysts through an end-to-end multi-stage pipeline:

```
[ Raw Security Events ]
          │
          ▼
┌───────────────────────────┐
│  Fast Anomaly Detector    │ ──► Isolation Forest (Numeric & behavioral features)
└─────────┬─────────────────┘
          │
          ▼
┌───────────────────────────┐
│  Event Correlator         │ ──► Graph & Time-Window Aggregator (MITRE ATT&CK TTPs)
└─────────┬─────────────────┘
          │
          ▼
┌───────────────────────────┐
│  Composite Risk Scorer    │ ──► 0-100 Score = Anomaly + Asset Criticality + Severity
└─────────┬─────────────────┘
          │
          ▼
┌───────────────────────────┐
│  RAG Knowledge Retriever  │ ──► ChromaDB Vector Store (CVEs, MITRE Tactics, Playbooks)
└─────────┬─────────────────┘
          │
          ▼
┌───────────────────────────┐
│  LLM Reasoning Engine     │ ──► Google Gemini Flash (Cached & On-Demand Explanations)
└─────────┬─────────────────┘
          │
          ▼
┌───────────────────────────┐
│  Mitigation Engine        │ ──► Concrete CLI / Firewall / Containment Commands
└─────────┬─────────────────┘
          │
          ▼
[ Real-Time SOC Dashboard (Next.js 14) ]
```

---

## Features

- **⚡ Fast-Path Anomaly Detection**: High-throughput Isolation Forest model classifying events in sub-milliseconds.
- **🔗 Smart Attack-Chain Correlation**: Clusters disparate events across network hosts and time windows into actionable Incidents mapped to MITRE ATT&CK.
- **🎯 Dynamic Composite Risk Scoring**: Calculates normalized risk scores ($0-100$) factoring in asset value, anomaly confidence, blast radius, and historical frequency.
- **📚 Security Knowledge RAG**: ChromaDB semantic search over curated security playbooks, CVE catalogs, and threat intelligence feeds.
- **🧠 Explainable AI Incident Reasoning**: Plain-English, step-by-step incident explanations explaining *What Happened*, *Root Cause*, and *Immediate Impact*.
- **🛡️ Actionable Mitigation Playbooks**: Automated generation of exact remediation steps, firewall rules, and containment commands.
- **🖥️ SOC Analyst Dashboard**: Cyberpunk/Glassmorphic dark UI built with Next.js 14, Tailwind CSS, Lucide icons, live event streams, incident filters, and instant demo replay.

---

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, Scikit-learn, ChromaDB, LangChain, Google Gemini API
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Radix UI, Lucide React
- **Storage**: SQLite (relational incidents/events), ChromaDB (vector embeddings)

---

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Node.js 18.x or higher & npm
- Google Gemini API Key (optional for live LLM explanations; pre-generated demo data included)

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Linux / macOS
   python -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and supply your GEMINI_API_KEY if desired
   ```

5. **Initialize Database and Knowledge Base**:
   ```bash
   # From the project root
   python scripts/build_knowledge_base.py
   python scripts/reset_demo_db.py
   ```

6. **Start the FastAPI Server**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend API will be available at `http://localhost:8000` (API Docs: `http://localhost:8000/docs`).

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env.local
   ```

4. **Start the Next.js development server**:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

---

## Project Structure

```
├── backend/
│   ├── api/                 # FastAPI routes (incidents, ingest, stats, settings, pregen)
│   ├── correlation/         # Event correlation and attack-chain grouping
│   ├── database/            # SQLAlchemy DB models and session management
│   ├── demo_data/           # Static demo telemetry and pre-generated AI explanations
│   ├── detection/           # Feature extraction & Isolation Forest anomaly detection
│   ├── llm/                 # Gemini prompt builders, explainer & incident cache
│   ├── mitigation/          # Mitigation recommendation generators
│   ├── models/              # Pydantic schemas (events, incidents, settings)
│   ├── rag/                 # ChromaDB retriever and knowledge base
│   ├── scoring/             # Composite risk scoring formulas
│   ├── tests/               # Test suites (unit, integration, e2e)
│   ├── main.py              # FastAPI application entrypoint
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── app/                 # Next.js App Router (pages, layout, globals.css)
│   ├── components/          # Reusable UI components (Incidents, Metrics, Ingest, Settings)
│   ├── lib/                 # Utility functions & API clients
│   └── tailwind.config.ts   # Styling tokens & glassmorphism theme
├── scripts/                 # Utility scripts (KB builder, demo generator, verifications)
└── README.md                # Project documentation
```

---

## Running Tests

Run the test suite to verify backend pipeline components:

```bash
pytest backend/tests -v
```

---

## Demo Scenario: "Operation Shadow DB"

ThreatIQ comes with a built-in end-to-end multi-stage APT demonstration called **Operation Shadow DB**:
1. **Reconnaissance**: Fast internal port scan on database asset.
2. **Credential Stuffing**: High-volume authentication failure burst.
3. **Lateral Movement**: Off-hour privileged database login.
4. **Data Exfiltration**: Multi-gigabyte outbound encrypted transfer.
5. **Persistence**: Unauthorized C2 reverse shell connection and shadow account creation.

You can trigger this live through the UI's **Demo Scenarios** button or reset with:
```bash
python scripts/reset_demo_db.py
```

---

## License

This project is licensed under the MIT License.
