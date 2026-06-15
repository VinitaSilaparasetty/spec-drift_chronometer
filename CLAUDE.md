# CLAUDE.md — Spec-Drift Chronometer

This file is for Claude Code. It documents the architecture, decisions made, and
instructions for continuing work in future sessions.

---

## Project Context

**Aevoxis Warden Engine: Spec-Drift Chronometer**
Top 300 finalist in the AWS 10,000 AIdeas Competition 2025.
Built by Vinita Silaparasetty, AI Governance Engineer, Aevoxis Solutions (aevoxis.de).

The product demonstrates EU AI Act Articles 12, 13, 14 & 50 compliance engineering:
real-time drift detection between human-authored architectural specs and AI-generated
code, with a Human-in-the-Loop Justification Gate that blocks execution until a human
approves or rejects the drift.

Live demo: https://spec-drift-chronometer.aevoxis.de

---

## Repository Layout

```
spec-drift_chronometer/
├── backend/
│   ├── main.py              # FastAPI Warden Engine — single file, all logic here
│   ├── requirements.txt     # fastapi, mangum, pydantic, uvicorn
│   ├── Procfile             # web: uvicorn main:app --host 0.0.0.0 --port 8080
│   ├── Dockerfile           # Lambda container image (public.ecr.aws/lambda/python:3.12)
│   └── provision_ledger.sh  # DynamoDB Intent Ledger setup script
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx         # Root page — polls /drift every 3s, passes state down
│   │   └── layout.tsx       # App shell — fonts, metadata, viewport
│   ├── src/components/
│   │   ├── DriftDashboard.tsx   # Main UI — chart, stat cards, logs, spec vault
│   │   ├── JustificationGate.tsx # Article 14 modal — submit justification, show result
│   │   └── GovernanceActions.tsx # Run Audit / Download Audit buttons
│   ├── next.config.ts       # output: 'export' + reactCompiler: true
│   ├── package.json         # Next.js 16, React 19, Tailwind 4
│   └── public/
│       ├── icon.png
│       └── manifest.json
├── .kiro/
│   ├── steering/            # Human-authored spec vault (governance.md, tech.md, etc.)
│   └── audit/last_sync.audit  # Written by backend on every audit/gate event
├── screenshots/
│   ├── 01-dashboard.png         # Sovereign Dashboard (normal state)
│   ├── 02-justification-gate-approved.png  # Gate APPROVED with reasoning trace
│   └── README.md
├── dev.sh                   # One-command launcher for local dev
├── pyproject.toml           # uv/hatch project definition
├── uv.lock                  # uv lock file
└── .env.example             # Documents all environment variables
```

---

## Architecture

### Backend — `backend/main.py`

Single FastAPI app. No database required for DEMO_MODE.

**In-memory state machine** (`_demo_state`):
- `gate_status`: `CLEAR → TRIGGERED → PENDING → RESOLVED`
- Resets to `CLEAR` on backend restart (intentional — each demo session is fresh)

**Demo scenario loop** (`_demo_scenarios`):
- 23 pre-scripted `(drift_value, status_label)` pairs cycling through:
  SOVEREIGN → MONITORING → CRITICAL_DRIFT (gate triggers) → GATE_PENDING → RESOLVING → SOVEREIGN
- Advances on every `/drift` poll, pauses when gate is TRIGGERED or PENDING

**Approval logic** (DEMO_MODE):
- Justification > 20 chars → APPROVED, Intent Alignment Score 91/100
- Justification ≤ 20 chars → REJECTED, Intent Alignment Score 29/100

**Production path** (`DEMO_MODE=false`):
- Calls `amazon.nova-pro-v1:0` via boto3 on AWS Bedrock, eu-central-1
- Falls back gracefully if credentials missing

**API routes:**
```
GET  /drift           — advance demo, return drift + gate state
GET  /gate/status     — current gate state + last decision
POST /gate/submit     — submit justification, invoke Warden, append to audit file
POST /audit           — write full ASCII audit report to .kiro/audit/last_sync.audit
GET  /download-audit  — serve audit file as download
GET  /specs           — return .kiro/steering/ file contents
```

Audit file path: `.kiro/audit/last_sync.audit` (relative to project root, resolved
from `backend/../.kiro/audit/`).

### Frontend — Next.js 16 / React 19 / Tailwind 4

Fully client-side. `output: 'export'` in `next.config.ts` — compatible with
Cloudflare Pages static deployment. No `getServerSideProps`, no server actions,
no API routes.

**Data flow:**
1. `page.tsx` polls `GET /drift` every 3 seconds via `useEffect`
2. Passes `driftData`, `currentStatus`, `gateStatus`, `currentDrift`, `demoMode`
   down to `DriftDashboard`
3. `DriftDashboard` auto-shows `JustificationGate` modal when `gateStatus === "TRIGGERED"`
4. `JustificationGate` POSTs to `/gate/submit`, shows APPROVED/REJECTED result inline
5. `GovernanceActions` POSTs to `/audit` then opens `/download-audit` in new tab

**All components are `"use client"`** — no hydration concerns.

**API URL:** `process.env.NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).
Written to `frontend/.env.local` by `dev.sh`. Must be set at build time for
static export since it's a `NEXT_PUBLIC_` variable baked into the bundle.

### Deployment

| Target | How |
|--------|-----|
| Local dev | `DEMO_MODE=true ./dev.sh` |
| Backend on any PaaS | `Procfile`: `web: uvicorn main:app --host 0.0.0.0 --port 8080` |
| Backend on AWS Lambda | `Dockerfile` (ECR Lambda Python 3.12 base), handler: `main.handler` via Mangum |
| Frontend on Cloudflare Pages | `npm run build` → deploy `out/` directory |

**Note:** Mangum (`from mangum import Mangum; handler = Mangum(app)`) is imported in
production to wrap FastAPI for Lambda. It is listed in `requirements.txt` but the
`handler` export must be wired at the bottom of `main.py` if Lambda deployment is
activated.

---

## Spec Vault — `.kiro/steering/`

These files are the human-authored architectural intent that the Warden cross-references:

| File | Purpose |
|------|---------|
| `governance.md` | Warden persona, negotiation protocol |
| `tech.md` | Technology constraints — region, models, runtimes |
| `product.md` | Vision and strategic pillars |
| `human-intent-specs.md` | INTENT-001 through INTENT-006 declarations |
| `spec.json` | Machine-readable thresholds and model config |
| `structure.md` | Repository structure intent |
| `boilerplate-standards.md` | Code standards |

The backend loads these via `_load_spec_intent()` and they are available at `GET /specs`.

---

## How to Run Locally

```bash
# DEMO_MODE — no AWS needed
DEMO_MODE=true ./dev.sh

# Production — requires AWS credentials in .env
cp .env.example .env
# fill in AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION=eu-central-1
DEMO_MODE=false ./dev.sh
```

`dev.sh` does:
1. Creates `venv/`, installs `backend/requirements.txt`
2. Starts uvicorn on port 8000, logs to `backend.log`
3. Writes `frontend/.env.local`
4. Installs `node_modules` if needed, starts Next.js on port 3000, logs to `frontend.log`

**To reset the demo gate cycle:** restart only the backend process. The frontend does not
need to restart.

```bash
kill $(lsof -ti:8000)
source venv/bin/activate && DEMO_MODE=true python -m uvicorn backend.main:app \
  --host 0.0.0.0 --port 8000 --reload &
```

**To take a screenshot of the Justification Gate Approved state:**
A Playwright script exists at `/Users/apple/tmp_playwright/gate_screenshot.js`.
It requires the backend to be freshly started (gate in CLEAR state) and the
frontend on port 3000. Run `node gate_screenshot.js` — it waits for drift to
rise (~30s), submits a justification, and saves the screenshot.

---

## Decisions Made in This Session

### Screenshot pipeline
- Moved screenshots from `docs/screenshots/` to `screenshots/` (root)
- Deleted `docs/` folder entirely
- Deleted `drif.webp` placeholder image
- Captured `02-justification-gate-approved.png` live from the running app using
  Playwright (`chromium` via Google Chrome headless), not a static mock

### README structure
- Added Live Demo section near the top
- Renamed "Main Dashboard" → "Sovereign Dashboard"
- Added "Justification Gate Approved" section with live screenshot
- Added "Sample Audit Trail Output" section with real ASCII audit content
- Removed redundant `## Screenshots` section (screenshots are inline)
- Removed `## About` section (duplicated by GitHub sidebar)
- Removed `Mode: DEMO_MODE (simulated)` from the audit code block in README;
  added a one-line prose note below instead

### License
- Changed from a restrictive evaluation-only license to **AGPL-3.0**
- Added commercial licensing contact line under the License section in README

### Static export
- Added `output: "export"` to `frontend/next.config.ts` for Cloudflare Pages
- No code refactoring needed — the entire frontend was already client-side

### Repo hygiene
- Added `*.bak` to `.gitignore`
- Removed `frontend/README.md` (boilerplate, superseded by root README)
- Removed `frontend/src/app/page.tsx.bak` (committed backup — should never have been tracked)
- Deleted local untracked junk: `recovery_temp/`, root `steering/` duplicate,
  `backend/main.py.bak`, `backend/test_results.log`, and all Python packages
  that had been installed directly into `backend/` (Lambda build artifacts from
  `pip install -r requirements.txt -t backend/` run in the wrong directory)
- Created `backend/Procfile` for PaaS deployment

### Conflict resolution
During a `git pull --rebase`, the remote had independently moved screenshot paths
and updated the license. Conflict in `README.md` was resolved by keeping the
"Sovereign Dashboard" rename over the remote's "Main Dashboard" label.

---

## Known Issues / Watch Points

- **Gate state is in-memory only.** Restarting the backend resets `gate_status` to
  `CLEAR`. This is fine for demo but means the gate cycle always restarts from scratch.
  If you need persistence across restarts, wire `_demo_state` to a file or DynamoDB.

- **`NEXT_PUBLIC_API_URL` is baked at build time.** For Cloudflare Pages, this env var
  must be set in the Cloudflare Pages build settings before `npm run build` runs.
  The static export cannot read runtime environment variables.

- **Mangum handler not currently exported.** `main.py` imports Mangum in
  `requirements.txt` but the `handler = Mangum(app)` line for Lambda is not in
  the current `main.py`. Add it at the bottom if deploying to Lambda.

- **`backend.log` and `frontend.log`** are written to the project root by `dev.sh`.
  They are gitignored (`*.log`) but will appear in `git status` if you generate them.
  This is expected.

- **`frontend/.env.local`** is auto-generated by `dev.sh` and gitignored by
  `frontend/.gitignore`. Never commit it.

- **`uv.lock` and `pyproject.toml`** are tracked. They define the project for the
  `uv` package manager. `dev.sh` uses plain `venv`/`pip` instead. Both can coexist.

---

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `DEMO_MODE` | `true` | `false` requires AWS credentials |
| `DRIFT_THRESHOLD` | `0.0075` | Gate triggers above this value |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Baked at build time |
| `AWS_ACCESS_KEY_ID` | — | Production only |
| `AWS_SECRET_ACCESS_KEY` | — | Production only |
| `AWS_REGION` | `eu-central-1` | Must be Frankfurt for data sovereignty |

See `.env.example` for the full list.
