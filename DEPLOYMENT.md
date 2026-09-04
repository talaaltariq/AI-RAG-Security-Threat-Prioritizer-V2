# ThreatIQ — Production Deployment Guide

Deploy the **frontend to Vercel** and the **backend to Render**, connected over HTTPS.

---

## 1. Read this first — how the app deploys

ThreatIQ is two applications, and they cannot live on the same platform:

| Part | What it is | Where it deploys | Why |
|---|---|---|---|
| `frontend/` | Next.js 14 dashboard | **Vercel** | Vercel's native framework — zero config needed. |
| `backend/` | FastAPI API (SQLite DB, ChromaDB vector store, scikit-learn model, LangChain + Gemini) | **Render** (free tier) | Vercel serverless functions cap bundles at 250 MB — this backend's dependencies (chromadb, scikit-learn, pandas, langchain) are far larger. It is also **stateful** (SQLite + ChromaDB on disk) and its ingest pipeline can run up to 120 s — serverless cannot host it. |

```
Browser ──> https://<your-app>.vercel.app        (Next.js frontend, on Vercel)
                     │  HTTPS (CORS-checked)
                     └──> https://threatiq-backend.onrender.com   (FastAPI, on Render)
                                  ├── SQLite (threatiq.db)
                                  ├── ChromaDB (backend/data/chroma_db)
                                  └── Google Gemini API (LLM + embeddings)
```

You will end up with two URLs; the frontend is the one you share with people.

### What was already prepared in this repo (no action needed)

- `backend/main.py` — CORS origins now come from the `CORS_ORIGINS` env var (comma-separated, or `*`). Unset, it behaves exactly as before (only `http://localhost:3000`), so local development is unchanged.
- `backend/main.py` — optional `CHROMA_PERSIST_DIR` env var lets you relocate the ChromaDB store onto a persistent disk later.
- `render.yaml` — Render Blueprint that pre-configures the backend service (Python 3.11, build/start commands, health check).
- `frontend/.env.example` / `backend/.env.example` — document every deployment variable.

---

## 2. Prerequisites (one-time, ~5 minutes)

1. **GitHub repo** — you already have it: `https://github.com/talaaltariq/AI-RAG-Security-Threat-Prioritizer-V2`.
2. **Vercel account** — sign up at <https://vercel.com/signup> using **Continue with GitHub**.
3. **Render account** — sign up at <https://render.com> using **GitHub** (no credit card needed for the free tier).
4. **Gemini API key** — get one at <https://aistudio.google.com/apikey> (Google AI Studio → "Get API key"). You may already have this in `backend/.env` locally.

---

## 3. Step 0 — Commit and push these changes

Render and Vercel both deploy **from GitHub**, so the deployment changes must be pushed first.

From the repo root (`d:\Projects\AI-RAG-Security-Threat-Prioritizer-Pro`):

```powershell
git add backend/main.py backend/.env.example frontend/.env.example render.yaml DEPLOYMENT.md
git commit -m "Prepare app for production deployment (Vercel frontend + Render backend)"
git push origin main
```

> `.env` / `.env.local` files are git-ignored — they never leave your machine. Secrets are set in the Render/Vercel dashboards instead (Step 1 / Step 2).

---

## 4. Step 1 — Deploy the backend on Render (~10 minutes)

### 1A. Create the service (Blueprint method — recommended)

1. Log in at <https://dashboard.render.com>.
2. Click **New +** (top right) → **Blueprint**.
3. Select the repository **AI-RAG-Security-Threat-Prioritizer-V2** → click **Connect**.
   (If it is not listed, click **Configure account** and grant Render access to that repo.)
4. Render reads `render.yaml` and shows one service: `threatiq-backend`. It prompts for the values marked `sync: false`:
   - **GEMINI_API_KEY** — paste your Gemini API key.
   - **GOOGLE_API_KEY** — paste the same key (or leave empty; optional).
   - **CORS_ORIGINS** — for now enter `http://localhost:3000`. You will replace this with your Vercel URL in Step 3.
5. Leave the plan on **Free** and the region as-is → click **Apply**.

### 1B. Alternative — manual method (if you prefer not to use the Blueprint)

**New + → Web Service** → connect the repo, then fill in exactly:

| Setting | Value |
|---|---|
| Name | `threatiq-backend` |
| Language / Runtime | Python 3 |
| Region | Any (closest to you) |
| Branch | `main` |
| Build command | `pip install -r backend/requirements.txt` |
| Start command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health` |
| Instance type | Free |

Then open **Environment** and add:
`PYTHON_VERSION` = `3.11.9`, `GEMINI_API_KEY` = *(your key)*, `CORS_ORIGINS` = `http://localhost:3000`.
Click **Create Web Service**.

### 1C. What the first deploy looks like

- **Build phase (3–7 min):** pip installs the Python dependencies (chromadb, sklearn, langchain are big).
- **Boot phase (~1–2 min):** the app creates the SQLite tables, trains the IsolationForest anomaly model (the `.pkl` is git-ignored, so it trains itself on first boot — by design), and indexes the MITRE ATT&CK + CVE knowledge base into ChromaDB using Gemini embeddings. This is normal; it happens once per fresh disk.
- The dashboard events feed turns green when the service is live.

### 1D. Verify the backend

Open `https://threatiq-backend.onrender.com/health` (replace `threatiq-backend` with your service name if different) — you should see:

```json
{"status": "ok", "version": "1.0.0"}
```

Optionally open `https://threatiq-backend.onrender.com/docs` to confirm the OpenAPI page renders.

**Copy and save the backend URL** — you need it in Step 2.

> Free-tier note: the service **sleeps after ~15 min of inactivity**; the first request after sleep takes ~30–60 s while it wakes. This is expected.

---

## 5. Step 2 — Deploy the frontend on Vercel (~5 minutes)

1. Log in at <https://vercel.com> → click **Add New… → Project**.
2. Under *Import Git Repository*, find **AI-RAG-Security-Threat-Prioritizer-V2** → click **Import**.
   (If not listed: *Adjust GitHub App Permissions* and grant Vercel access to the repo.)
3. On the Configure Project screen — **this is the critical part**:
   - **Root Directory** → click **Edit** → select **`frontend`** → Continue.
     (Without this, Vercel cannot find the Next.js app and the build fails.)
   - Framework Preset, Build Command, Output Directory: leave auto-detected (**Next.js** / `next build`).
4. Expand **Environment Variables** and add:

   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://threatiq-backend.onrender.com` |

   Check the **Production**, **Preview**, and **Development** boxes so all deployments use it.

5. Click **Deploy** and wait ~2–3 minutes for the build to finish.
6. Click **Continue to Dashboard → Domains** and copy your URL, e.g. `https://ai-rag-security-threat-prioritizer-v2.vercel.app`.

> **Important:** `NEXT_PUBLIC_*` variables are baked into the JavaScript **at build time**. If you ever change `NEXT_PUBLIC_API_URL`, you must redeploy (Deployments → ⋯ → Redeploy) for it to take effect.

---

## 6. Step 3 — Connect the two (CORS)

The backend currently only allows `http://localhost:3000`. Your Vercel domain must be whitelisted:

1. In the **Render** dashboard → open **threatiq-backend** → **Environment**.
2. Edit **CORS_ORIGINS** and set it to your exact Vercel URL:

   ```
   https://ai-rag-security-threat-prioritizer-v2.vercel.app
   ```

   - Multiple origins are allowed, comma-separated, e.g.
     `https://your-app.vercel.app,http://localhost:3000`
   - URL must include `https://` and **no trailing slash**.
3. Click **Save Changes** — Render redeploys automatically (~2–3 min).

> Preview deployments (from branches/PRs) get extra URLs like `https://<project>-git-<branch>-<team>.vercel.app`. If you want previews to reach the backend too, add those URLs to `CORS_ORIGINS`, or temporarily use `*` (allows any origin — fine for a demo, avoid for real production).

---

## 7. Step 4 — Seed data and verify end-to-end

1. Open your **Vercel URL**. First visit redirects to the **/setup** page.
2. **Section 1 — Upload your data:** upload `backend/demo_data/demo_events.json`.
   - Get it from GitHub: your repo → `backend/demo_data/demo_events.json` → **Download raw file** (or use any `.json`/`.csv` security event file).
   - The first upload may take up to a minute if the backend is waking from sleep.
3. **Section 2 — Configure your LLM:** pick provider **Google Gemini**, a model (e.g. `gemini-1.5-flash`), and paste the API key → **Test Connection** → must show a green success.
4. Click **Run Analysis** → the threat queue loads.

Final verification checklist:

- [ ] `https://<backend>.onrender.com/health` returns `{"status": "ok", ...}`
- [ ] Dashboard shows KPI cards, alert-volume chart, severity distribution
- [ ] Threat queue lists incidents; opening one shows score breakdown, AI explanation, RAG citations
- [ ] **Export Report** downloads a PDF
- [ ] Settings page loads knowledge-base stats (MITRE / CVE document counts)

If everything passes, your app is live. 🎉

---

## 8. Environment variable reference

**Render (backend)**

| Variable | Required | Value / default |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Gemini API key (LLM + embeddings) |
| `CORS_ORIGINS` | Yes | Your Vercel URL(s), comma-separated; `*` = allow all |
| `PYTHON_VERSION` | set by blueprint | `3.11.9` |
| `GOOGLE_API_KEY` | No | Alternative to `GEMINI_API_KEY` |
| `EMBEDDING_MODEL` | No | Default `models/gemini-embedding-001` |
| `LLM_MODEL` | No | Default `gemini-3.6-flash` |
| `DATABASE_URL` | No | Default `sqlite:///./threatiq.db` |
| `CHROMA_PERSIST_DIR` | No | Only for persistent-disk setups (see §9) |

**Vercel (frontend)**

| Variable | Required | Value |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | `https://<backend>.onrender.com` |

---

## 9. Production notes you should know

- **Free-tier data is ephemeral.** On Render Free, every deploy/restart gives the service a fresh filesystem: the SQLite DB, ChromaDB index, and trained model reset. The app self-heals (re-creates tables, retrains the model, re-indexes the knowledge base on boot) but **incidents are gone** — simply re-run the /setup flow (Step 4) to reload demo data. Re-indexing also consumes a small amount of Gemini embedding quota (~23 documents) on each cold boot.
- **Persistence upgrade path (optional):** upgrade the Render service to a paid plan (Starter), attach a **Disk** mounted at `/var/lib/threatiq`, then set:
  - `DATABASE_URL=sqlite:////var/lib/threatiq/threatiq.db` (note: four slashes for an absolute path)
  - `CHROMA_PERSIST_DIR=/var/lib/threatiq/chroma_db`
- **Keep a single uvicorn worker** (the default start command). The app uses SQLite and in-memory caches — multiple workers would corrupt state.
- **Gemini quota:** each ingestion generates live LLM explanations for uncached incidents. If you hit the free daily quota, explanations degrade gracefully to a low-confidence error result — the app keeps working.
- **Secrets:** never commit `.env` files; set secrets only in the Render/Vercel dashboards.
- **Custom domains:** Vercel → Project → Settings → Domains; Render → Service → Settings → Custom Domains. If you attach a custom domain to the frontend, remember to add it to `CORS_ORIGINS`.

---

## 10. Updating the deployment

```powershell
git add <changed files>
git commit -m "Describe the change"
git push origin main
```

- **Vercel** auto-builds every push to `main`.
- **Render** auto-deploys every push to `main` (Auto-Deploy is on by default).

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Dashboard card: *"Unable to reach the ThreatIQ API"* | `NEXT_PUBLIC_API_URL` missing/wrong, or backend asleep | Check the var in Vercel → redeploy; confirm `/health` opens in a browser; wait ~60 s for Render cold start and refresh. |
| Browser console: *blocked by CORS policy* | Vercel URL not in `CORS_ORIGINS` | Add the exact URL (with `https://`, no trailing slash) on Render → save. |
| Vercel build fails: *No Next.js app detected* | Root Directory not set | Project Settings → Root Directory = `frontend`, redeploy. |
| Render deploy fails: *No module named 'backend'* | Service configured with a sub-directory/root dir | Remove any Root Directory override — the start command must run from the repo root. |
| First request after idle times out / 502 | Render free tier waking up | Retry after a minute. |
| `503 Threat pipeline is not available` | Detector failed to boot | Render → Events/Logs tab → read the traceback (usually a bad Python version — ensure `PYTHON_VERSION=3.11.9`). |
| Dashboard empty after a backend redeploy | Ephemeral disk reset (expected on free tier) | Visit `https://<frontend>.vercel.app/setup` and re-upload the demo data. |
| Uploads rejected as too large | 5 MB / 1000-event cap is by design | Split the file. |

---

## 12. Local development (unchanged)

```powershell
# Terminal 1 — backend (repo root)
venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

`frontend/.env.local` (`NEXT_PUBLIC_API_URL=http://localhost:8000`) keeps pointing the dev UI at your local backend, and the backend's default `CORS_ORIGINS` still allows `http://localhost:3000` — nothing about your local workflow changes.
