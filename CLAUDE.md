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
│   ├── requirements.txt     # fastapi, mangum, pydantic, uvicorn, google-generativeai, requests
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
├── test_research/
│   ├── drift_calculator.py      # Standalone drift scorer (gitpython, no backend needed)
│   ├── run_tests.py             # 3-phase test runner: drift / justification / audit
│   ├── run_failure_modes.py     # 8 EU AI Act failure mode tests (FM1,FM3-FM6,FM10-FM12)
│   ├── requirements.txt         # requests, gitpython, pandas, tabulate
│   ├── README.md                # How to run, relationship to IEEE paper
│   └── results/                 # All test run outputs (committed for paper reproducibility)
│       ├── failure_modes_summary.md   # IEEE paper data table
│       ├── failure_modes_raw.txt      # Full test run output
│       ├── raw_results_mistral.txt    # 9-justification Mistral test results
│       └── audit_trail/               # Gate audit files from each test run
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
- Production drift scorer: `_score_diff_locally_production()` — linear mapping
  `0.001 + raw * 0.013`. Gate triggers at raw token divergence ≥ ~52%.
  Do NOT use `_map_drift_score()` for production diffs — that function is
  calibrated for the 23 pre-crafted demo sample diffs only.

**WARDEN_LLM override** (`WARDEN_LLM` env var):
When set, `/gate/submit` routes justification evaluation to a real LLM instead
of `_bedrock_analyze()`. Handled by `_warden_llm_analyze()`. Supported values:
- `gemini` — uses `GEMINI_API_KEY`, model `gemini-1.5-flash` via google-generativeai
- `huggingface` — uses `HF_API_KEY`, model `meta-llama/Llama-3.1-8B-Instruct:auto`
  via `router.huggingface.co` (requires HuggingFace Pro account)
- `mistral` — uses `MISTRAL_API_KEY`, model `mistral-small-latest`
  via `api.mistral.ai/v1/chat/completions` (OpenAI-compatible)

All three backends use the same prompt template and return the same response shape.
If the LLM call fails with a network/auth error, the exception is caught and the
error is embedded in `reasoning_trace` — the endpoint still returns HTTP 200
REJECTED. This is a known Article 17 silent failure (see Known Issues).

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

### WARDEN_LLM — real LLM backends for research
Added `WARDEN_LLM` env var that routes `/gate/submit` to a real LLM. Implemented
`_warden_llm_analyze()` in `main.py` with three backends: gemini, huggingface,
mistral. The DEMO_MODE path and `_bedrock_analyze()` are completely untouched —
WARDEN_LLM only activates when the env var is explicitly set.

HuggingFace notes: `api-inference.huggingface.co` is DNS-blocked in some sandboxed
environments. Use `router.huggingface.co` instead. The router requires a Pro
account — free-tier keys return `{"error": "Invalid username or password."}`.
Model name needs the `:auto` suffix: `meta-llama/Llama-3.1-8B-Instruct:auto`.

Mistral works reliably from all environments tested: `api.mistral.ai`,
`mistral-small-latest`, OpenAI-compatible response format.

### Production drift scorer fix
The original production path used `_map_drift_score()` which is calibrated for
demo sample diffs. For real git diffs, tokens like `ledger`, `immutable`, and
`verification` appear in both the spec vault (357 tokens) and diff output, giving
raw divergence of ~0.70 which maps to 0.0072 — just below the 0.0075 threshold.
Fix: `_score_diff_locally_production()` with linear formula `0.001 + raw * 0.013`.
Gate triggers when raw ≥ ~0.52. Committed in `7a92016`.

### test_research/ folder — IEEE Software paper data
Created `test_research/` with three components:
1. `drift_calculator.py` — standalone drift scorer using gitpython, no backend needed
2. `run_tests.py` — 3-phase test runner (drift across 5 commits, 9 justification
   quality levels WEAK/MEDIUM/STRONG, audit trail generation)
3. `run_failure_modes.py` — 8 EU AI Act failure mode tests

Ran all 9 justification tests with Mistral. Results: WEAK justifications scored
0–5/100 (REJECTED), MEDIUM scored 10/100 (REJECTED), STRONG scored 91–95/100
(APPROVED). Results saved in `test_research/results/raw_results_mistral.txt`.

### Failure mode test suite
Ran 8 failure mode tests against Articles 12, 13, 14, 17 with Mistral key.
Results: 6 CONFIRMED, 1 MITIGATED (FM10), 1 PARTIAL (FM12).

Key findings:
- **FM3 CONFIRMED** — 10-line spec vault injection reduced drift 61% (0.0113→0.0044),
  dropping below the 0.0075 threshold. Detection for entire vocabulary domain silenced.
- **FM5 CONFIRMED** — commit scoring 0.0064 (85% of threshold) produces zero audit entry
- **FM6 CONFIRMED** — 3-commit sequence, zero commit SHAs in audit trail
- **FM11 CONFIRMED** — invalid Mistral key returns HTTP 200 REJECTED with
  `{"detail":"Unauthorized"}` buried in `reasoning_trace`. Two silent failure paths:
  (1) invalid LLM key caught by `except Exception` at `main.py:545`,
  (2) boto3 unavailable also returns HTTP 200 REJECTED silently.
- **FM1 CONFIRMED** — score 40/100 REJECTED; gate evaluated text quality only, no identity/role check.
- **FM10 MITIGATED** — Mistral caught the MD5/bcrypt factual error (score 20/100).
  But this is a conditional mitigation: the gate prompt asks for "justification
  adequacy" not "technical accuracy". Mitigation depends on LLM training coverage.
- **FM4 CONFIRMED** — drift score identical before (0.0126) and after (0.0126) two
  gate submissions. Spec vault never updated by gate decisions.

All test commits were reverted after each test. Results committed in `b69474a`.

Note: FM1 score was 5/100 with `mistral-small-2412` and 40/100 with `mistral-small-2506`.
FM10 score was 10/100 with 2412 and 20/100 with 2506. Verdicts (CONFIRMED / MITIGATED)
are identical across both models. `mistral-small-2412` was deprecated 2026-06; the
pinned model was updated to `mistral-small-2506` in commit `b467c89`.

### test_research/.gitignore — results unblocked
Removed `results/` from `test_research/.gitignore` (commented it out with note)
so test results can be committed for IEEE paper reproducibility. The gitignore
still blocks `*.env`, `secrets.py`, `keys.py`, and `*_key.txt`.

### README updates
Added `WARDEN_LLM` and three API key rows to the Environment Variables table.
Added `## Research` section documenting `test_research/`, both test runners,
and the FM3 headline stat. Committed in `2790126`.

### Reproducibility fixes — model pin and temperature
Pinned the Mistral model from the floating `"mistral-small-latest"` tag to the
specific versioned alias `"mistral-small-2506"` and added `"temperature": 0` to
the payload in `_warden_llm_analyze()`. Both changes are in `main.py` lines 509–551.

Why this matters: `mistral-small-latest` silently changes when Mistral releases a
new version. `temperature=0` removes sampling randomness so the same model produces
identical outputs across runs. Together these make 7 of the 8 failure mode findings
fully deterministic for anyone reproducing the IEEE paper results.

FM10 (MITIGATED) remains conditionally reproducible — it holds for `mistral-small-2506`
specifically because that model's training data covers the MD5/bcrypt vulnerability.
A different model version may not catch it. The README documents this caveat.

Committed in `81c2af2`. `test_research/README.md` updated to reflect pinned model
and to replace the "±5–10 points variation" note with the determinism guarantee.

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

- **FM11 silent failure is not fixed.** When `WARDEN_LLM` is set and the LLM
  returns a 4xx error, `_warden_llm_analyze()` catches it in `except Exception`
  (line 545 of `main.py`) and returns a REJECTED response with the error buried
  in `reasoning_trace`. `/gate/submit` cannot distinguish this from a legitimate
  REJECTED and returns HTTP 200. The frontend sees `decision: REJECTED` in both
  cases. Fix: check `resp.status_code` before `raise_for_status()` and return
  `{"http_error": f"Mistral API {resp.status_code}"}` for 4xx — this triggers
  the HTTP 500 path that already exists in `gate_submit()`.

- **FM3 spec vault has no tamper-evidence.** Anyone with write access to
  `.kiro/steering/` can add vocabulary to suppress drift detection for any code
  domain. No integrity check or access control exists on the spec vault files.

- **Near-miss events (FM5) leave no audit trail.** The audit file is only written
  by `/gate/submit` and `POST /audit`. Commits that score below the threshold
  produce no log entry, making escalating near-miss patterns invisible
  retrospectively.

- **Gate has no authentication (FM1).** `/gate/submit` accepts requests from any
  caller with network access. There is no middleware to verify the submitter's
  identity, role, or authority. Anyone who writes a spec-aligned justification
  will receive the same APPROVED decision as a senior architect.

- **Rollback target not in audit (FM6).** The audit file contains drift value,
  justification, decision, model, and timestamp — but no commit SHA, branch, or
  file list. When multiple commits trigger the gate cumulatively, operators cannot
  identify which commit to roll back without manual `git bisect`.

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
| `WARDEN_LLM` | *(unset)* | Route gate evaluation to real LLM: `gemini`, `huggingface`, `mistral` |
| `GEMINI_API_KEY` | — | Required when `WARDEN_LLM=gemini` |
| `HF_API_KEY` | — | Required when `WARDEN_LLM=huggingface` (Pro account needed) |
| `MISTRAL_API_KEY` | — | Required when `WARDEN_LLM=mistral` |

See `.env.example` for the full list.
