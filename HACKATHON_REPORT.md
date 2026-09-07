# ThreatIQ — Hackathon Project Report

## 1. Title & Team Info

- **Project:** ThreatIQ — AI-Powered Security Threat Prioritizer
- **Team:** Talal Tariq and Saad Khan
- **Event:** Alibaba AI Hackathon, in partnership with Al Khidmat Foundation

## 2. Executive Summary

ThreatIQ is a triage assistant for security analysts who are drowning in alerts. It takes raw security events (JSON, CSV, Syslog-style telemetry), detects anomalous behavior with an Isolation Forest model, groups related events into multi-stage attack incidents, and ranks each incident with a transparent 0–100 risk score. For the incidents that matter most, it pulls relevant MITRE ATT&CK techniques and CVEs from a local vector database and asks an LLM to write a structured, evidence-grounded explanation. The result is a dashboard where an analyst sees a short, ranked queue of real incidents instead of a wall of disconnected alerts — plus one-click PDF reports for management.

## 3. Problem Statement

Security Operations Centers deal with alert fatigue. A single SIEM can produce thousands of alerts a day, most of them false positives, and the alerts arrive as isolated events with no sense of how they relate to each other. A port scan, a burst of failed logins, and an odd outbound connection might be one coordinated attack — but three different analysts might look at each one separately and close all three as noise.

The consequences are real: genuine intrusions get buried, analyst time is wasted on duplicates, and "why is this urgent?" is answered with gut feeling instead of evidence. We wanted to build something that does the tedious correlation and prioritization automatically, and — just as important — explains its reasoning so the analyst can trust it.

## 4. Solution Overview

We built an end-to-end pipeline: ingest raw events, score each one for anomalous behavior, cluster suspicious events into attack-chain incidents, compute a composite risk score, enrich high-priority incidents with retrieval-augmented LLM analysis, and present everything in a web dashboard. Crucially, the LLM never decides what's dangerous on its own — the scoring is pure math, and the LLM only explains and contextualizes what the pipeline already found.

## 5. Key Features

- **Anomaly detection:** scikit-learn Isolation Forest scores every event with a configurable cutoff threshold (5%–95%), tuned from the settings page.
- **Attack-chain correlation:** a temporal-window and host/identity clustering engine stitches related alerts into single incidents, mapped to MITRE ATT&CK techniques.
- **7-factor composite risk score (0–100):** base severity, anomaly confidence, asset criticality, exploitability, evidence count, recency, and threat-intel relevance — each factor shown to the analyst as a point breakdown, not a black box.
- **RAG-grounded AI explanations:** ChromaDB holds MITRE tactics, techniques, mitigations, and CVE summaries. Explanations follow a strict 4-tier format: Observed Evidence, Retrieved Context, AI Interpretation, Recommended Action.
- **Multi-provider LLM support:** Google Gemini, OpenAI, Anthropic Claude, Groq, and local Ollama, switchable at runtime with a live connection test.
- **Human-in-the-loop lifecycle:** incidents move through Active → Under Review → Contained → Resolved with an audit trail.
- **Executive PDF reports:** a ReportLab-based generator produces audit-ready incident reports.
- **Demo mode:** ships with "Operation Shadow DB," a five-phase simulated APT (recon → credential stuffing → lateral movement → C2 → exfiltration) so judges can see the full pipeline without real data.

## 6. Tech Stack

**Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy + SQLite, Pydantic v2, scikit-learn, pandas/NumPy, ChromaDB (vector store), LangChain (langchain-google-genai, langchain-openai), fpdf2 for PDFs, pytest.

**Frontend:** Next.js 14 (App Router), React 18, TypeScript 5, Tailwind CSS v3 with shadcn/ui (Radix primitives), Recharts, SWR + Axios for data fetching, Framer Motion, lucide-react icons.

## 7. System Architecture

The system has three layers. The **processing pipeline** (Python) is a thin orchestrator that wires modules together: normalizer → Isolation Forest detector → event correlator → risk scorer → RAG retriever → LLM explainer → SQLite persistence. The **API layer** (FastAPI routers) exposes incidents, ingestion, upload, stats, settings, LLM config, and PDF reports as REST endpoints. The **presentation layer** (Next.js) has four screens: an executive dashboard with KPIs and alert-volume charts, a threat queue ranked by score, an incident deep-dive page with the score dial and AI analysis, and a settings page for thresholds and model config.

A useful way to picture it: raw events flow down the pipeline and come out the other side as scored, explained incidents in SQLite; the frontend only ever talks to FastAPI, never to the ML or LLM code directly.

## 8. How It Works

1. An analyst uploads a `.json` or `.csv` telemetry file (or events arrive through the ingest API).
2. Each event is normalized into a common schema — timestamps, IPs, host, action — then scored by the Isolation Forest. Events above the anomaly cutoff get flagged.
3. The correlator groups flagged events that share hosts, identities, or time windows into incidents and attaches MITRE technique mappings.
4. The risk scorer computes the 0–100 composite score. The pipeline also scans the event evidence for grounded signals (e.g., "reverse shell," "C2 domain") to set the exploitability and threat-intel flags honestly.
5. High and Critical incidents get RAG retrieval and an LLM explanation; everything below the band gets a deterministic rule-based explanation so no incident is ever left blank.
6. The analyst opens the dashboard, sees the queue sorted by score, drills into an incident, reads the 4-tier explanation with citations, and can contain, resolve, or export it to PDF.

## 9. Challenges Faced

**LLM cost and latency.** Calling an LLM for every incident was slow and burned through the Gemini free-tier quota fast — retry loops made it worse. We restructured so the LLM only runs at or above the configurable High threshold, added a pre-caching toggle that generates explanations at ingest time, and built a deterministic rule-based fallback. Every incident gets an explanation even with no API key at all.

**Keeping the LLM honest.** Early prompts let the model invent context. We fixed this by grounding every explanation in retrieved ChromaDB documents and enforcing the 4-tier output structure, so "Retrieved Context" always cites real MITRE technique IDs or CVEs. We also hit embedding-model mismatches between indexing and retrieval (404s from renamed models), which taught us to pin one embedding model for both paths.

**PDF generation edge cases.** fpdf2's text APIs don't wrap the way you'd expect — long remediation text overflowed the page until we switched to `multi_cell` with explicit cursor resets. Unglamorous, but the report is what management actually reads.

## 10. What We Learned

The biggest lesson: in a security product, the AI should be the last step, not the first. Getting the deterministic layers right — correlation, scoring, retrieval — mattered far more than prompt quality. We also learned that "explainability" is a feature you have to engineer deliberately: showing the point breakdown of the score built more trust than any paragraph the LLM wrote. On the practical side, we got much better at structuring a FastAPI backend into testable modules and at designing fallbacks so an external API failure never takes the product down.

## 11. Future Improvements

- Train the Isolation Forest on larger, real-world datasets and retrain on a schedule instead of shipping a static model.
- Deeper SIEM integrations (Splunk, Elastic) so ingestion is continuous rather than file-upload based.
- User authentication and multi-tenant support for team deployments.
- Streaming explanations so long LLM outputs appear progressively in the UI.
- Automated containment actions (firewall rule push, host isolation) with approval gates, turning recommendations into one-click execution.

## 12. Conclusion

ThreatIQ turns an overwhelming alert stream into a short, ranked, explainable incident queue. The heavy lifting — detection, correlation, scoring — is deterministic and transparent; the AI sits on top to retrieve evidence and explain it in plain language. We're proud that the system works end-to-end even without an LLM key, and we think that design choice is what would make it trustworthy in a real SOC.
