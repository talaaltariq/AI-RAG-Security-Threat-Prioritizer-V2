# Presentation Specification — ThreatIQ: AI-Powered Security Threat Prioritizer Pro

> This document is a complete, self-contained specification for an AI presentation generator.
> It describes exactly 8 slides, their content, explanations, visuals, and layout.
> All facts below are verified against the actual project source code, README, and UI screenshots.
> Do not invent numbers, features, or technologies beyond what is stated here.

---

## Project Overview

**ThreatIQ** is an AI-powered Security Operations Center (SOC) triage assistant. It solves the problem of *alert fatigue*: security analysts receive thousands of isolated alerts per day, most of them noise, and must manually figure out which ones are part of a real attack.

ThreatIQ ingests raw security events (JSON/CSV logs), and runs them through a deterministic pipeline:

1. **Normalizes** each event into a common schema (timestamp, IPs, host, action, asset criticality).
2. **Detects anomalies** with an unsupervised machine-learning model (scikit-learn **Isolation Forest**) trained on synthetic "normal business hours" traffic; each event gets a 0.0–1.0 anomaly score against a configurable cutoff (default 0.5).
3. **Correlates** related events into multi-stage attack incidents using a union-find clustering algorithm: events are grouped when they share the same source IP with consecutive gaps of ≤ 15 minutes, or map to the same MITRE ATT&CK technique (e.g. authentication failures → T1110.001, port scans → T1046, data exfiltration → T1041, process spawning → T1059).
4. **Scores** each incident with a transparent **7-factor composite risk score (0–100)**: base severity (max 20), anomaly score (max 20), asset criticality (max 20), exploitability (max 15), evidence count (max 10), recency (max 10), and threat-intel relevance (max 5).
5. **Retrieves threat intelligence** via RAG (Retrieval-Augmented Generation): semantic vector search in a **ChromaDB** knowledge base containing 12 MITRE ATT&CK techniques and 11 CVE summaries.
6. **Explains** High/Critical incidents with a structured LLM output (Google Gemini by default; OpenAI-compatible providers supported) in four fixed sections — *Observed Evidence*, *Retrieved Context*, *AI Interpretation*, *Recommended Action* — plus a confidence rating. Lower-severity incidents get a deterministic rule-based explanation instead, so the AI never fabricates facts.
7. **Presents** everything in a Next.js 14 analyst dashboard: security overview, prioritized threat queue, incident deep-dive, tunable pipeline settings, and downloadable PDF incident reports.

**Tech stack (verified):** Python 3.11+ / FastAPI / SQLAlchemy + SQLite / scikit-learn / ChromaDB / LangChain (langchain-google-genai, langchain-openai) / ReportLab-family PDF generation (fpdf2) / Next.js 14 + TypeScript + Tailwind CSS v3 + shadcn/ui.

**Bundled demo scenario:** "Operation Shadow DB" — a simulated multi-stage attack on a production database (`prod-db-01`): port scan → credential stuffing → lateral movement → reverse shell → encrypted data exfiltration over a C2 channel. The demo dataset of 954 raw events is correlated into 606 incidents, of which 2 are prioritized as Critical (headline incident scores 91/100); the dashboard reports 36.5% alert-noise reduction for this dataset. **These numbers are demo-dataset-specific and must always be presented as such.**

**Available real project visuals** (use these in the slides; paths relative to the repository root):

- `docs/screenshots/01-setup-and-configuration.png` — first-run setup page (file upload + LLM provider configuration).
- `docs/screenshots/02-security-overview-dashboard.png` — main dashboard (954 events / 606 incidents / 2 critical / 36.5% alert reduction, alert velocity chart, severity breakdown).
- `docs/screenshots/03-threat-queue.png` — prioritized threat queue table ranked by risk score.
- `docs/screenshots/04-incident-ai-analysis.png` — incident deep-dive: 91/100 score dial, 7-factor score breakdown, 4-section AI analysis, threat-intel citations, event timeline.
- `docs/screenshots/05-pipeline-settings.png` — settings page with anomaly threshold slider and severity band controls.
- `frontend/public/logo-horizontal.png` and `frontend/public/logo-icon.png` — ThreatIQ brand logos (shield + bolt mark, "Threat" black + "IQ" lime).

---

## Presentation Goal

Enable a non-specialist audience (hackathon judges, managers, students, mixed technical/business listeners) to understand, in under 10 minutes:

1. The real-world problem (alert fatigue) and why it matters.
2. What ThreatIQ does, end to end, in plain language.
3. The three ideas that make it trustworthy: transparent scoring, attack-chain correlation, and AI explanations grounded in retrieved facts instead of free-form generation.
4. Concrete evidence from the running product (real screenshots and real demo numbers).

## Target Audience

General/mixed audience: hackathon judges, product managers, engineering leadership, and students. Assume familiarity with everyday computing but **no** background in cybersecurity, machine learning, or LLMs. Every technical term (anomaly detection, correlation, RAG, MITRE ATT&CK, CVE, composite score) must be explained in one plain sentence the first time it appears.

## Core Story

> **Security teams are drowning in alerts. ThreatIQ turns thousands of raw alerts into a short, ranked, explainable list of real threats — and shows its work.**

Narrative arc across the 8 slides:

1. **Hook / Title** — what ThreatIQ is in one sentence.
2. **Problem** — alert fatigue: too many alerts, too little context, real attacks get missed.
3. **Solution** — ThreatIQ as an AI triage layer: the 954 → 606 → 2 funnel from the demo.
4. **How it works** — the 7-stage pipeline as one clear flow diagram.
5. **The score** — the transparent 7-factor, 0–100 composite risk score.
6. **The explanation** — RAG-grounded, 4-section AI analysis with citations.
7. **The product in action** — real UI walkthrough (dashboard, queue, incident, settings).
8. **Conclusion** — why it is different, what the audience should remember.

---

## Design System

The presentation MUST follow the project's design system (`DESIGN_SYSTEM.md` — "Neo-Electric Slate & Obsidian"). Summary of the binding rules:

### Colors

| Role | Color | Hex |
| :--- | :--- | :--- |
| Dark surfaces (title slide background, hero stat cards, diagram chips) | Obsidian | `#0C0E12` |
| Secondary dark surface | Obsidian 800 | `#12141A` |
| Main light canvas (default slide background) | Ice Pearl | `#F4F7FC` |
| Card surfaces on light slides | White | `#FFFFFF` |
| Primary accent (headline highlights, key numbers, active elements, primary chart series) | Electric Lime | `#D8FA42` (surface variant `#DCF838`, light tint `#F4FDC6`) |
| Secondary accent (supporting data, diagrams, second chart series) | Cyber Teal | `#36C6AF` (light tint `#D5F6F0`) |
| Primary text on light | Near-black | `#12141A` |
| Secondary text / captions | Slate | `#7E8695` |
| Muted text | Light slate | `#A3ABB9` |
| Text on lime elements | Obsidian | `#0C0E12` |
| Severity accents (only when depicting severity) | Critical: red/pink family as in UI (`#F43F5E`-style chip), High: orange, Medium: teal, Low: soft green/teal |

### Typography

- Font family: **Plus Jakarta Sans** (fallback: Outfit, then Inter).
- Slide titles: 800 weight, tight letter-spacing (−0.03em), near-black on light slides, white on dark slides.
- Hero numbers: 800 weight, large.
- Body text: 400/500 weight; captions and labels: 500 weight in `#7E8695`.
- Code/technical tokens (e.g. `T1041`, `prod-db-01`): JetBrains Mono or SF Mono style.

### Geometry & Components

- Cards: 20–24px border-radius (`rounded-2xl`/`rounded-3xl`), soft shadow `0 4px 20px -2px rgba(18,38,63,0.03)`, no harsh borders.
- Pills: fully rounded (9999px) for tags, badges, and buttons.
- Signature element: **inverted obsidian KPI cards** — black cards with big white numbers and a lime pill footnote — reuse this for all key statistics on slides.
- Diagrams: rounded rectangles / pill nodes, thin 1.5–2px monoline icons, lime and teal as the only accent colors, soft slate for connectors and labels.
- Charts: borderless, smooth curves, lime + teal series, soft gridlines `#EFF3F8`, black pill tooltips.
- Generous whitespace; minimal visual clutter; no decorative stock imagery.

---

## Visual Language

- Alternate slide backgrounds for rhythm: dark obsidian for the title and conclusion slides; light ice-pearl canvas with white cards for content slides.
- Use the actual ThreatIQ logo (`frontend/public/logo-horizontal.png` or the icon on dark backgrounds) on the title and closing slides.
- All diagrams must be drawn in the design system's flat, rounded, lime/teal style — NOT generic clip-art or 3D illustrations.
- Screenshots from `docs/screenshots/` should be shown in white, 24px-radius frames with a soft shadow, like product cards.
- Every graphic must explain something: funnels show noise reduction, flow diagrams show the pipeline, stacked bars show score composition. No purely decorative graphics.
- Use short caption labels under every diagram in `#7E8695`.

---

# Slide 1 — ThreatIQ: From Alert Chaos to Clear Priorities

## Purpose

Introduce the product name, the one-sentence value proposition, and set the visual tone. After this slide the audience knows what the product is called and roughly what it does.

## Main Message

ThreatIQ is an AI-powered assistant that turns thousands of raw security alerts into a short, ranked, explainable list of real threats.

## Content

- ThreatIQ logo and product name.
- Title: "ThreatIQ — AI-Powered Security Threat Prioritizer".
- Subtitle: "Machine-learning detection, attack-chain correlation, transparent risk scoring, and AI explanations grounded in real threat intelligence."
- Three small keyword pills: "ML Anomaly Detection" · "MITRE ATT&CK Mapping" · "RAG-Grounded AI Explanations".
- Optional small footnote: "Open source · MIT/Apache 2.0".

## Explanation

The presenter says: "Security teams see thousands of alerts a day. ThreatIQ is a system that automatically reads those alerts, groups the ones that belong to the same attack, scores how dangerous each attack is, and explains — in plain language, with evidence — why. This presentation shows how it works."

## Graphics / Visuals

- Full-bleed obsidian (`#0C0E12`) background.
- Centered ThreatIQ logo (use `frontend/public/logo-icon.png` large, or horizontal logo).
- Behind/beside the logo: a subtle abstract motif of small lime and teal dots streaming in from the left (many, scattered) and converging into a few bright, ordered dots on the right — visual metaphor for "many alerts → few prioritized threats". Drawn flat, thin strokes, `rgba(255,255,255,0.08)` grid dots as texture. Keep it subtle.
- The three keyword pills at the bottom: dark chips (`#12141A`) with lime or teal 1px outline and white text.

## Visual Explanation

The converging-dots motif communicates the entire product in one glance: chaos in, order out. It must be abstract and minimal — not a literal screenshot — so the slide stays a clean title card.

## Layout Guidance

Centered composition. Logo + title in the upper-middle, subtitle directly below, keyword pills in a single row near the bottom third. At least 40% of the slide remains empty dark space. No body paragraphs.

## Important Elements

- Exact product name "ThreatIQ" with the capital IQ.
- The subtitle must not promise anything beyond detection, correlation, scoring, and explanation.

## Speaker / Presentation Context

Keep this slide short (30–45 seconds). Do not read the subtitle word for word; use the spoken explanation above.

---

# Slide 2 — The Problem: Security Teams Are Drowning in Alerts

## Purpose

Establish the pain point that motivates the project. After this slide the audience understands *why* a tool like ThreatIQ is needed.

## Main Message

Security Operations Centers receive so many isolated alerts every day that analysts cannot tell which ones matter — and real attacks hide in the noise.

## Content

- Headline: "Alert fatigue is the #1 bottleneck in security operations."
- Plain-language explanation of a SOC: "A Security Operations Center (SOC) is the team that watches a company's computers for attacks, 24/7."
- The three pain points (short bullets with icons):
  1. **Too many alerts** — thousands of raw alerts per day; industry studies report up to ~80% turn out to be false alarms (state this as a general industry problem, as documented in the project README — not as a ThreatIQ measurement).
  2. **No context** — each alert arrives alone; the analyst must manually figure out that "a port scan at 22:10, a failed login at 22:15, and a strange data transfer at 22:25" are actually one attack.
  3. **Real attacks get missed** — while analysts wade through noise, the few genuinely dangerous incidents wait in the same pile.
- Define "alert" in one line: "An alert is a single automated warning, e.g. 'someone failed to log in 50 times'."

## Explanation

"Imagine a hospital emergency room where every patient's monitor beeps all day, and 4 out of 5 beeps mean nothing. Nurses stop reacting. That's a modern SOC. The problem is not detecting suspicious things — tools detect plenty. The problem is deciding what deserves a human's attention *right now*."

## Graphics / Visuals

- **Before-picture graphic** (right half of slide): a stylized wall/stack of many small alert cards (30–40 tiny rounded rectangles in muted slate `#A3ABB9` on a white card). Almost all are grey; 2 of them glow critical-red/pink — visually invisible among the noise. A small magnifying-glass monoline icon with a tired/analyst glyph (simple flat person at a desk) at the base.
- Alternatively or additionally: a simple "alert volume vs. analyst capacity" concept: a tall lime bar labelled "Daily alerts" next to a tiny teal bar labelled "What a human can review".
- Do NOT use stock photos of hackers in hoodies.

## Visual Explanation

The grey alert wall with two hidden red alerts makes "the needle in the haystack" problem instantly visible without any numbers. The audience should feel the overload.

## Layout Guidance

Light slide (`#F4F7FC`). Left ~45%: headline + the three pain-point bullets, each with a small 1.5px monoline icon in a lime-tinted circle (`#F4FDC6`). Right ~55%: the alert-wall graphic inside a white 24px-radius card with soft shadow. One-sentence definition of "alert" as a caption under the bullets.

## Important Elements

- The "~80% false positives" figure must be attributed as a general industry problem (per the project README), never as a ThreatIQ result.
- Terms to define on-slide: *SOC*, *alert*.

## Speaker / Presentation Context

This is the emotional hook — spend a full minute here. Use the hospital-monitor analogy verbally. End with: "So the question is: how do you find the two red cards automatically?"

---

# Slide 3 — The Idea: An AI Triage Layer That Shows Its Work

## Purpose

Present ThreatIQ's solution concept at a high level, before any technical detail. After this slide the audience knows the "what" — the "how" comes next.

## Main Message

ThreatIQ sits between the raw alert stream and the analyst: it groups related alerts into attack stories, scores each one from 0–100, and lets the analyst start at the top of the list.

## Content

- Headline: "Thousands of alerts in. A short ranked list out."
- The demo funnel as the hero content (label it clearly as the bundled demo dataset):
  - **954** raw alerts processed → **606** correlated incidents → **2** critical threats prioritized → **36.5%** of alert noise eliminated.
- Three one-line promises (the product's differentiators):
  1. **Correlation** — alerts that belong to the same attack are stitched into one incident.
  2. **Transparent scoring** — every incident gets a 0–100 score whose math is fully visible.
  3. **Grounded AI explanations** — the AI explains using retrieved threat intelligence, with citations, not guesswork.
- One-line definition: "An *incident* is a group of related alerts that together describe one attack."

## Explanation

"ThreatIQ does not replace analysts — it queues their work. Think of a spam filter, but for attack alerts: instead of 954 beeps, the analyst opens a sorted to-do list. Two items at the top are marked Critical with a score of 91 out of 100, and clicking one shows exactly which alerts formed it, why it scored that high, and what to do about it."

## Graphics / Visuals

- **Funnel diagram (hero visual, center of slide):** three-to-four horizontal stages, drawn as rounded bars that shrink left to right:
  - Stage 1 bar (wide, muted slate outline): "954 raw alerts".
  - Stage 2 bar (medium, teal `#36C6AF`): "606 correlated incidents".
  - Stage 3 bar (small, lime `#D8FA42` with obsidian text): "2 critical threats".
  - Side callout pill (lime): "−36.5% alert noise".
- Under the funnel, three small white cards in a row, one per differentiator (Correlation / Transparent scoring / Grounded explanations), each with a monoline icon (linked-chain icon, calculator/gauge icon, book-with-sparkle icon).

## Visual Explanation

The shrinking funnel is the product's value in one shape: volume collapses, and what survives is bright (lime) and few in number. The three cards beneath answer "why trust it?" before the audience has to ask.

## Layout Guidance

Light slide. Funnel occupies the upper 55–60%, wide and centered, with big 800-weight numbers inside each bar. Differentiator cards in a row below. Footnote in muted text: "Numbers from ThreatIQ's bundled demo dataset." Keep each card to a title + one line.

## Important Elements

- Exact demo numbers: 954 → 606 → 2, and 36.5%.
- Mandatory caption that these figures come from the bundled demo dataset (accuracy requirement).
- The word "incident" must be defined on this slide.

## Speaker / Presentation Context

Emphasize the ordering of the story: "First it *groups*, then it *scores*, then it *explains*." This primes the audience for the pipeline on the next slide.

---

# Slide 4 — How It Works: The 7-Stage Analysis Pipeline

## Purpose

Explain the end-to-end mechanics in one picture. This is the technical heart of the presentation, but every stage must be described in plain language. After this slide the audience can retell the data flow.

## Main Message

Every raw event travels through seven clearly separated stages — from messy log line to explained, prioritized incident — and each stage has one job.

## Content

The pipeline stages (verified from `backend/pipeline.py`):

1. **Normalize** — different log formats (JSON, CSV) are converted into one standard event format (who, what, when, where, how important the target machine is).
2. **Detect anomalies (ML)** — an *Isolation Forest* model flags events that look unusual. Explain in one sentence: "An Isolation Forest is a machine-learning model that learned what normal office-hours activity looks like, and scores each event 0–1 for weirdness — e.g. a login at 3 AM from an unknown address with 50 failed attempts scores high."
3. **Correlate** — events from the same attacker (same source address, close in time — within a 15-minute window — or matching the same known attack technique) are grouped into one incident.
4. **Score** — each incident gets the 0–100 composite risk score (preview of the next slide).
5. **Retrieve intelligence (RAG)** — the system searches its built-in knowledge base (12 MITRE ATT&CK attack techniques + 11 known software vulnerabilities/CVEs) for documents that semantically match the incident.
6. **Explain (AI)** — for High/Critical incidents, a large language model writes a structured explanation using only the retrieved facts; lower-severity incidents get a deterministic, rule-based explanation.
7. **Store & present** — everything is saved to a database and shown on the analyst dashboard; PDF reports can be exported.

- Definitions on-slide (small caption row): *MITRE ATT&CK* = "a public encyclopedia of real attacker techniques"; *CVE* = "a public catalog of known software vulnerabilities"; *RAG* = "retrieve-then-generate: the AI may only write using documents the system just retrieved".

## Explanation

"Read the diagram left to right as one event's journey. A raw log line comes in, gets cleaned up, gets a weirdness score from the ML model, gets grouped with its siblings into an attack story, gets a danger score, gets matched against an encyclopedia of known attacks, and finally an AI writes the incident report. Every stage is a separate, testable module — the AI is only involved at the end, and only with retrieved facts in hand."

## Graphics / Visuals

- **Horizontal pipeline flow diagram (hero visual):** 7 rounded-rectangle nodes connected by arrows, left to right (wrap into two rows of 4 + 3 if needed). Node styling: white cards with 16–20px radius, thin slate border, a small monoline icon each; stage numbers in small obsidian pills (01–07).
- Color-code the stages by type: ML stage gets a teal icon accent (`#36C6AF`), the AI/LLM stage gets a lime accent (`#D8FA42`) with a small "AI" chip, storage stage shows a database icon.
- Above the first node: a small input chip "Raw security events (JSON / CSV)". After the last node: an output chip "Prioritized incidents + dashboard + PDF report".
- A subtle background band behind nodes 5–6 labelled "Grounded AI zone — uses only retrieved facts" in lime-tint (`#F4FDC6`).

## Visual Explanation

The audience should be able to trace one event with their finger. The "Grounded AI zone" band is the key conceptual device: it visually separates deterministic machinery (stages 1–4, 7) from AI reasoning (stages 5–6), reinforcing that the AI does not run wild over raw data.

## Layout Guidance

Light slide, diagram-first: the flow occupies the middle 60% of the slide at large scale. Headline and one-sentence intro on top. The three term definitions (MITRE ATT&CK, CVE, RAG) in a muted caption strip at the bottom. Keep per-stage text to a bold name + ≤ 8 words.

## Important Elements

- Stage names exactly as listed; the 15-minute correlation window; "0–1 weirdness score"; knowledge base contents "12 MITRE techniques + 11 CVEs"; the rule that LLM explanations apply to High/Critical incidents only.
- Do not add stages that don't exist (no "sandboxing", no "automatic blocking" — ThreatIQ recommends actions; humans execute them).

## Speaker / Presentation Context

Walk the diagram left to right slowly. If time is short, name all seven stages but expand only on stage 2 (ML) and stage 6 (AI) — the next two slides cover scoring and explanation in detail.

---

# Slide 5 — The Score: Transparent 0–100 Risk Math

## Purpose

Show that prioritization is not a black box: the score is a simple, auditable sum of seven understandable factors. After this slide the audience trusts the ranking.

## Main Message

Every incident's priority is a 0–100 score built from seven visible ingredients — an analyst can see exactly where every point came from.

## Content

- Headline: "No black box: 7 factors, 100 points, fully auditable."
- The factor table (verified from `backend/scoring/risk_scorer.py`):

| Factor | Max points | Plain-English meaning |
| :--- | ---: | :--- |
| Base severity | 20 | How severe the original alert was rated |
| Anomaly score | 20 | How unusual the ML model found the behavior |
| Asset criticality | 20 | How important the attacked machine is (a production database counts far more than a test laptop) |
| Exploitability | 15 | Whether attackers are known to have working exploit code for this technique |
| Evidence count | 10 | How many related events confirm the attack (more stages = more confidence) |
| Recency | 10 | How fresh the activity is (an attack 5 minutes ago outranks one from yesterday) |
| Threat-intel relevance | 5 | Whether the technique matches current threat intelligence |

- Severity bands: score ≥ 80 → **Critical**, ≥ 60 → **High**, ≥ 40 → **Medium**, below → **Low** (defaults; adjustable in Settings).
- Worked example from the real demo incident on `prod-db-01` (score 91/100): Base severity 20/20 · Anomaly 19/20 · Asset criticality 20/20 · Exploitability 15/15 · plus evidence, recency, and intel points = 91.

## Explanation

"Instead of one mysterious 'AI score', ThreatIQ adds up seven numbers a human can argue with. Was the target important? Is the behavior weird? Is there a known exploit? How much evidence? Each factor has a published maximum, so a score of 91 means the incident maxed out almost every category. And the thresholds that turn a score into Critical/High/Medium/Low are sliders in the settings page — the security team tunes its own sensitivity."

## Graphics / Visuals

- **Stacked horizontal bar (hero visual):** one bar from 0 to 100 showing the demo incident's 91 points as stacked segments (lime `#D8FA42` for the three 20-point factors, teal `#36C6AF` for exploitability, obsidian `#12141A` or muted tints for the rest), each segment labelled with its points. The empty 9-point remainder shown in light grey.
- Beside/below the bar: the factor table rendered as compact rows with capsule progress fills (alternating lime/teal) — in the design system's table style.
- A small "severity bands" strip: four colored segments (Low/Medium/High/Critical) with threshold markers at 40/60/80.
- Optional small inset crop of the Score Breakdown panel from `docs/screenshots/04-incident-ai-analysis.png` as proof it exists in the UI.

## Visual Explanation

The stacked bar makes "score = sum of parts" literal — the audience sees 91 assembled in front of them. The UI screenshot inset proves the math is surfaced to real users, not just an internal formula.

## Layout Guidance

Light slide. Headline top-left. Left ~55%: stacked bar large + severity band strip beneath it. Right ~45%: compact factor table card (white, 24px radius). Keep table rows to factor name, max points, and a ≤ 8-word gloss.

## Important Elements

- Exact point values (20/20/20/15/10/10/5) and the 80/60/40 default thresholds.
- The real example: prod-db-01, 91/100, with at least the four top factors' points.
- Mention that thresholds are configurable.

## Speaker / Presentation Context

Emphasize auditability: "In a security product, a score you can't explain is a score you can't defend to your boss or an auditor." This slide usually earns the most trust — give it time.

---

# Slide 6 — The Explanation: AI Grounded in Real Threat Intelligence

## Purpose

Explain the RAG approach and the structured 4-section explanation — the feature that makes the AI output trustworthy. After this slide the audience understands why the AI can't simply invent things.

## Main Message

The AI never writes from memory: the system first retrieves matching attack-technique and vulnerability documents, then the AI must structure its answer into Evidence → Context → Interpretation → Action — with citations and a confidence rating.

## Content

- Headline: "AI that shows its sources."
- RAG in one sentence: "**RAG (Retrieval-Augmented Generation)** means: look up the relevant facts first, then let the AI write — using only those facts."
- The knowledge base: 12 MITRE ATT&CK techniques and 11 CVE vulnerability summaries, stored as searchable vectors in ChromaDB. Explain "vector search" plainly: "the database finds documents by *meaning*, not just matching keywords."
- The four fixed sections of every AI analysis (verified from `backend/llm/explainer.py` and the UI):
  1. **Observed Evidence** — what actually happened, drawn from the telemetry (which machine, which events, which IPs).
  2. **Retrieved Context** — what the threat-intelligence database says about these techniques (e.g. "T1041 = Exfiltration Over C2 Channel"), each with a relevance percentage.
  3. **AI Interpretation** — what it means: attacker's likely goal and stage of the attack.
  4. **Recommended Action** — concrete next steps, e.g. "isolate prod-db-01 from the network immediately".
- Guardrails worth naming: the model is constrained to a fixed structured format; a confidence rating (High/Medium/Low) is attached; if the AI is unavailable or the incident is below the High threshold, a deterministic rule-based explanation is used instead; the UI footer states "AI-generated analysis. Verify before acting."

## Explanation

"Chatbots hallucinate — everyone knows that. ThreatIQ's answer is retrieval: before the AI writes a word, the system pulls the matching pages from its attack encyclopedia — here, the MITRE entry for data exfiltration over command-and-control channels, with a 73% relevance score. The AI's job is reduced to connecting those cited facts to the observed events. And the answer always comes in the same four labeled boxes, so an analyst can check the evidence box against the raw events in one glance."

## Graphics / Visuals

- **Use the real screenshot** `docs/screenshots/04-incident-ai-analysis.png` as the primary visual, framed in a white card with soft shadow. Annotate it with 3–4 small callout labels pointing to: the 91/100 score dial, the four analysis sections, the threat-intelligence citations with "73% relevant" pills, and the event timeline.
- Optionally, a small left-side mini-diagram: "Incident → search knowledge base → retrieved documents (T1041, T1059.001, T1573, CVEs) → AI writes 4 sections" as a compact 3-step flow.

## Visual Explanation

The annotated screenshot is proof, not decoration: the audience sees that every concept from the previous slides (score, factors, citations, timeline) lives in one real screen. Callouts should use lime pills with obsidian text and thin connector lines.

## Layout Guidance

Light slide. Screenshot large on the right ~60%, annotated. Left ~40%: headline, RAG definition sentence, and the four sections as a numbered list with tiny colored left-border chips (teal for Evidence, blue/teal for Context, purple or lime for Interpretation, lime for Action — matching the UI's accent borders). Bottom: the guardrail notes as one muted caption line.

## Important Elements

- The four section names verbatim.
- Real retrieved citations from the demo: T1041 (Exfiltration Over C2 Channel), T1059.001 (PowerShell), T1573 (Encrypted Channel), CVE-2023-34362, CVE-2020-1472 — with relevance percentages (73%, 72%, 72%, 69%, 68%).
- The "verify before acting" disclaimer and the confidence badge.

## Speaker / Presentation Context

This is the differentiator slide — most "AI for security" demos skip grounding. Say explicitly: "The AI is the last step, not the first. Deterministic math decides the score; the AI only explains it with cited sources."

---

# Slide 7 — The Product in Action: A 4-Screen Analyst Workflow

## Purpose

Show that the pipeline ends in a real, usable product. After this slide the audience has seen the complete user journey and knows how a human interacts with the system.

## Main Message

From first-run setup to a resolved incident, the entire workflow lives in four clean screens: Setup → Dashboard → Threat Queue → Incident Detail — plus a Settings page to tune the engine.

## Content

The workflow, screen by screen:

1. **Setup** (`docs/screenshots/01-setup-and-configuration.png`) — drag-and-drop upload of `.json`/`.csv` event files and LLM provider configuration with a connection test. The API key is used only for the connection test, never stored.
2. **Security Overview Dashboard** (`docs/screenshots/02-security-overview-dashboard.png`) — headline KPIs (954 events, 606 incidents, 2 critical, 36.5% noise reduction on the demo dataset), alert-volume-over-time chart, severity distribution, and a one-click **Export Report** (PDF).
3. **Threat Queue** (`docs/screenshots/03-threat-queue.png`) — all incidents sorted by risk score, filterable by severity band, searchable by asset/IP/technique; each row shows score badge, target asset, MITRE technique, event count, and status.
4. **Incident Detail** (`docs/screenshots/04-incident-ai-analysis.png`) — the deep dive from slide 6, plus the **Analyst Actions**: Acknowledge / Escalate / Resolve (incident lifecycle: Active → Under Review → Contained → Resolved).
5. **Pipeline Settings** (`docs/screenshots/05-pipeline-settings.png`) — sliders for anomaly-detection sensitivity (5%–95%) and severity score thresholds; changes persist immediately.

## Explanation

"The analyst's day looks like this: upload logs once, open the dashboard to see the security posture at a glance, then work the threat queue top-down — highest score first. Clicking an incident shows the evidence, the AI analysis, and the timeline; the analyst acknowledges, escalates, or resolves it, and exports a PDF report for management. Tuning knobs live in Settings, not in code."

## Graphics / Visuals

- **Screenshot strip / carousel (hero visual):** the 4 key screenshots (setup, dashboard, queue, incident detail) shown as framed cards in a horizontal 2×2 grid or an overlapping fan, each with a numbered lime pill (1–4) and a one-line caption. Include the settings screenshot smaller, or as a 5th card if space allows.
- A thin progress arrow along the top: "Setup → Overview → Queue → Deep Dive → Action".

## Visual Explanation

Seeing four real, polished screens in sequence communicates maturity better than any claim — the audience understands it's a working product, not a concept. Numbered pills tie each screen to one workflow step.

## Layout Guidance

Light slide. Screenshots dominate (~70% of the area). Workflow arrow across the top. Captions minimal — one line per screen. Do not paste walls of feature text; the screens speak.

## Important Elements

- All five screenshot files listed above; at minimum setup, dashboard, queue, and incident detail must appear.
- Demo numbers on the dashboard shot must keep the "demo dataset" framing if quoted in captions.

## Speaker / Presentation Context

Narrate as a day-in-the-life, not a feature list. If presenting live, this is where a 60-second live demo would replace the screenshots — mention that option to the presenter.

---

# Slide 8 — Why It Matters & What to Remember

## Purpose

Close with the value summary and the three memorable ideas. After this slide the audience can repeat what ThreatIQ is and why it's different.

## Main Message

ThreatIQ turns alert overload into a ranked, evidence-backed to-do list — fast deterministic machinery for detection and scoring, AI only where it explains, always with sources.

## Content

- Headline: "From 954 alerts to 2 priorities — with the reasoning attached." (demo dataset)
- Three takeaway cards:
  1. **Correlation beats volume** — related alerts become one attack story, cutting noise by 36.5% on the demo dataset.
  2. **Transparent beats magical** — a 0–100 score with seven visible factors and tunable thresholds, auditable by design.
  3. **Grounded beats generated** — AI explanations built only on retrieved MITRE/CVE intelligence, with citations and confidence ratings.
- Tech stack strip (small, muted): "FastAPI · scikit-learn Isolation Forest · ChromaDB vector search · Google Gemini / OpenAI-compatible LLMs · Next.js 14 · SQLite · PDF reports".
- Closing line + logo; optional: "Open source — MIT/Apache 2.0" and QR/link placeholder for the repository.

## Explanation

"If you remember three things: it groups, it scores transparently, and its AI shows sources. ThreatIQ doesn't try to replace the analyst — it hands them a short list where the top item is the attack, the math is visible, and the recommended first action is already written."

## Graphics / Visuals

- Return to the dark obsidian slide treatment for bookend symmetry with slide 1.
- Echo the title-slide motif inverted: a few bright, ordered lime dots on the left (the prioritized threats) with the faint grey swarm behind them — "order out of chaos".
- Three takeaway cards as inverted obsidian KPI-style cards (dark cards, white bold text, lime pill labels) — the design system's signature component.
- ThreatIQ logo centered at the bottom with the closing line.

## Visual Explanation

The dark bookend signals "the end" and makes the three takeaway cards glow. Reusing the dots motif gives the deck a deliberate visual arc: chaos → order.

## Layout Guidance

Dark slide, centered composition. Headline top, three takeaway cards in a row in the middle, tech-stack strip as small muted text, logo + closing line at the bottom. Minimal text overall.

## Important Elements

- The three takeaways verbatim.
- Tech stack list exactly as verified — do not add technologies (no Kubernetes, no Redis, no GPT claims beyond "OpenAI-compatible").
- "Demo dataset" qualifier on any repeated numbers.

## Speaker / Presentation Context

End with the spoken summary above, then pause. If Q&A follows, likely questions to prep for: "Does it block attacks automatically?" (No — it recommends; a human acts, via the Acknowledge/Escalate/Resolve workflow.) "Does it need an AI API key?" (It ships with pre-generated demo intelligence; a Gemini or OpenAI-compatible key enables live explanations.)

---

## Final Presentation Guidelines

1. **Slide count:** exactly 8 slides, in the order specified. Do not split or merge.
2. **Accuracy:** every number, feature, factor, threshold, and citation in this spec is verified against the repository. Do not add statistics, benchmarks, customer claims, or capabilities that are not listed here. The figures 954 / 606 / 2 / 36.5% must always carry the "bundled demo dataset" qualifier.
3. **Language:** plain English for a non-technical audience. Every technical term (SOC, alert, incident, Isolation Forest, correlation, composite score, RAG, vector search, MITRE ATT&CK, CVE, LLM) must be explained in one sentence at first use — use the explanations provided in each slide's Content/Explanation sections.
4. **Text balance:** each slide pairs one hero visual with scannable text. No paragraph longer than 3 lines on any slide; prefer bullets, pills, and captions.
5. **Design system compliance:** backgrounds only in `#0C0E12` (dark slides 1 & 8) or `#F4F7FC` (light slides); cards white, 20–24px radius, soft shadows; accents limited to Electric Lime `#D8FA42` and Cyber Teal `#36C6AF`; typography in Plus Jakarta Sans (fallback Outfit/Inter) with 800-weight titles; pills fully rounded; no harsh borders, no gradients beyond subtle tints, no stock photography, no clip-art hackers/hoodies/padlocks.
6. **Graphics with purpose:** funnel (slide 3), pipeline flow (slide 4), stacked score bar (slide 5), annotated screenshot (slide 6), screenshot strip (slide 7) are mandatory and must match their descriptions. Decorative-only imagery is prohibited.
7. **Real screenshots:** use the five files in `docs/screenshots/` and the logos in `frontend/public/` exactly as assigned per slide. Frame them as white 24px-radius cards with the design system's soft shadow.
8. **Consistency:** identical title style, caption style, and pill style across all slides; severity colors (Critical red/pink, High orange, Medium teal, Low green/teal) used only when depicting severity values.
9. **Speaker notes:** include each slide's "Speaker / Presentation Context" as presenter notes in the generated deck.
