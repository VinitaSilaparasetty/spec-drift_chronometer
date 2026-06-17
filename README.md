*Developed for the AWS 10,000 AIdeas Competition 2025 |
Top 300 Finalist from over 10,000 global submissions*

**Built by Vinita Silaparasetty, AI Governance Engineer |
Aevoxis Solutions | aevoxis.de**

[Read the official project submission on AWS Community Builder](https://builder.aws.com/content/3ArZsXU7l4aaXPzFdXH0DdlyaM4/aideas-spec-drift-chronometer)

---

## Live Demo

[Try the Spec-Drift Chronometer](https://spec-drift-chronometer.aevoxis.de)

Running in DEMO_MODE. No AWS credentials required.
Backend processing in Frankfurt, EU Central.

---

# Aevoxis Warden Engine: Spec-Drift Chronometer


### Sovereign Dashboard

![Sovereign Dashboard — Spec-Drift Chronometer](screenshots/01-dashboard.png)

> Normal operating state. Drift is within threshold, system status reads SOVEREIGN, and all governance indicators are green. The complete system at a glance: drift variance chart, sovereign spec vault, warden activity log, and governance action buttons on a single screen.

### Justification Gate Approved

![Justification Gate Approved — Spec-Drift Chronometer](screenshots/02-justification-gate-approved.png)

> The complete governance cycle in one frame. Drift has crossed the sovereign threshold, a human submitted a substantive justification, and the Warden Agent returned an APPROVED decision with Intent Alignment Score 91/100 and a full reasoning trace cross-referenced against `.kiro/steering/`. This is Article 14 Human-in-the-Loop enforcement working end-to-end.

**Aevoxis Warden Engine** — an AI governance platform that detects semantic drift
between human-authored architectural intent and AI-generated code in real time.
Compliant with **EU AI Act Articles 12, 13, 14 & 50** (Transparency and Human Oversight).

---

## EU AI Act Alignment

| Requirement | Implementation |
|---|---|
| Article 14: Human Oversight | Justification Gate blocks execution until human approval |
| Article 12: Record Keeping | Deterministic audit trail exported on every governance decision |
| Article 13: Transparency | Real-time drift coefficient visible to all stakeholders |
| Article 50: Disclosure | System identifies itself as AI-governed at every interaction point |

---

## What This Solves

Enterprises deploying autonomous AI systems face a critical
governance problem: how do you detect when an AI system has
drifted from its original human-approved specification, and
how do you enforce accountability when it does?

The Spec-Drift Chronometer monitors autonomous AI outputs in
real time, detects misalignment between human intent and system
behaviour, and triggers a Human-in-the-Loop Justification Gate
before any non-compliant action is executed.

EU AI Act Article 14 human oversight requirements are engineered
directly into the architecture, not added as an afterthought.
Deployed on Render (backend) and Cloudflare Pages (frontend).
AWS Lambda deployment is also supported via the included Dockerfile and Procfile.

---

## What It Does

| Feature | Description |
|---------|-------------|
| **Drift Detection** | Polls a live drift index every 3 seconds. Visualises it as a real-time bar chart coloured by severity. |
| **Justification Gate** | When drift crosses the sovereign threshold, an Article 14-compliant Human-in-the-Loop gate appears. No automated merge proceeds without human sign-off. |
| **Warden Agent** | Submits the human justification to Amazon Nova Pro (or a realistic mock in DEMO_MODE) and returns a structured reasoning trace. |
| **Audit Trail** | Every governance event is logged to `.kiro/audit/last_sync.audit` with a SHA-256 verification hash — downloadable from the dashboard. |
| **Spec Vault** | Human intent specs live in `.kiro/steering/`. The Warden cross-references every decision against these files. |

---

## Connecting to Your Production AI System

The Spec-Drift Chronometer is designed to wrap around AI systems a client already has running — it does not replace the AI pipeline, it governs it. The example below uses a LangChain RAG chatbot, one of the most common enterprise AI deployments, to illustrate exactly how the connection works. The same integration pattern applies to any LangChain-compatible pipeline.

### How it works

```
User query
    │
    ▼
Your LangChain RAG chain
    │
    ├── WardenCallbackHandler.on_chain_start()
    │         │
    │         ▼
    │     GET /drift  →  check gate status
    │         │
    │         ├── gate = CLEAR    →  proceed normally
    │         └── gate = TRIGGERED →  raise WardenGateBlockedException
    │                                 (execution halted — human sign-off required)
    ▼
Retrieval → Generation → Response
```

When the Warden detects that the committed code has drifted from the
human-authored spec (`.kiro/steering/`), it sets the gate to `TRIGGERED`.
The callback picks this up on the next chain call and raises an exception
that halts generation until an operator opens the governance dashboard,
submits a justification, and receives Warden Agent approval.

### Integration — three files, one line that matters

```bash
cd integrations/langchain_rag
pip install -r requirements.txt
```

```python
from warden_client import WardenClient
from warden_callback import WardenCallbackHandler

warden = WardenClient(base_url="https://your-warden-api.example.com")
handler = WardenCallbackHandler(warden, dashboard_url="https://your-dashboard.example.com")

# ← This single line wires EU AI Act Article 14 governance into your chain
rag_chain = (your_existing_chain).with_config(callbacks=[handler])
```

### Behaviour at the gate

When the gate triggers, the chatbot returns a structured message instead
of generating an answer:

```
╔══════════════════════════════════════════════════════════╗
║  WARDEN GATE BLOCKED — Execution halted (Article 14)    ║
╚══════════════════════════════════════════════════════════╝
  Drift index : 0.0091
  Threshold   : 0.0075
  Gate status : TRIGGERED

  Action required: open the governance dashboard and submit
  a justification to the Warden Agent before retrying.

  Dashboard → https://spec-drift-chronometer.aevoxis.de
```

The operator submits a justification via the dashboard. The Warden Agent
(Amazon Nova Pro) evaluates it against the spec files and returns
APPROVED or REJECTED with an Intent Alignment Score. Once approved,
the gate clears and the chatbot resumes accepting queries.

### Full working example

`integrations/langchain_rag/rag_chatbot.py` is a complete LangChain RAG chatbot
with FAISS vector store, OpenAI or fake LLM (no API key required for demo),
and the Warden callback pre-wired.

```bash
# Demo mode — fake LLM, no OpenAI key needed. Requires Warden running locally.
OPENAI_API_KEY=demo python integrations/langchain_rag/rag_chatbot.py

# Live mode — real OpenAI + real Warden
WARDEN_API_URL=https://your-warden.example.com \
OPENAI_API_KEY=sk-... \
python integrations/langchain_rag/rag_chatbot.py
```

### Integration directory

```
integrations/
└── langchain_rag/
    ├── requirements.txt     # langchain-core, langchain-community, faiss-cpu
    ├── warden_client.py     # Thin HTTP client for the Warden API
    ├── warden_callback.py   # LangChain BaseCallbackHandler (the integration point)
    └── rag_chatbot.py       # Complete working example
```

The same `WardenCallbackHandler` pattern works with any LangChain-compatible
chain — LangGraph agents, OpenAI Assistants via LangChain, custom LCEL pipelines.
The Warden API is framework-agnostic: any HTTP client can call `/drift` and
`/gate/submit` directly.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | ≥ 3.12 | `python3 --version` |
| Node.js | ≥ 18 | `node --version` |
| npm | ≥ 9 | bundled with Node.js |
| curl | any | used by `dev.sh` health-check |

No AWS account needed for DEMO_MODE.

---

## Quickstart — DEMO_MODE (under 5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/VinitaSilaparasetty/spec-drift_chronometer.git
cd spec-drift_chronometer

# 2. Make the launcher executable (first time only)
chmod +x dev.sh

# 3. Launch everything with a single command
DEMO_MODE=true ./dev.sh
```

The script will:
1. Create a Python venv and install backend dependencies
2. Start the FastAPI Warden Engine on **port 8000**
3. Write `frontend/.env.local` pointing at localhost
4. Start the Next.js dashboard on **port 3000**

Open **http://localhost:3000** in your browser.

**Demo flow (automatic, ~45 seconds):**
1. Dashboard loads — drift is low, system status is SOVEREIGN
2. Drift rises through MONITORING into CRITICAL_DRIFT
3. The **Justification Gate** modal appears automatically
4. Type any meaningful justification and click **Submit to Warden Agent**
5. The Warden (mocked Nova Pro) returns APPROVED or REJECTED with a reasoning trace
6. Click **Run Audit** then **Download Audit** to see the full audit trail

---

## Production Setup — Live AWS Bedrock

### 1. Configure AWS credentials

```bash
cp .env.example .env
# Edit .env and set:
#   AWS_ACCESS_KEY_ID=...
#   AWS_SECRET_ACCESS_KEY=...
#   AWS_REGION=eu-central-1
#   DEMO_MODE=false
```

### 2. IAM permissions required

```
bedrock:InvokeModel         (on amazon.nova-pro-v1:0 and amazon.nova-lite-v1:0)
dynamodb:PutItem            (optional — for persisting the Intent Ledger)
dynamodb:GetItem
```

### 3. Start with real credentials

```bash
DEMO_MODE=false ./dev.sh
```

### 4. Deploy to AWS Lambda

```bash
cd backend
pip install -r requirements.txt -t package/
zip -r ../deployment_package.zip main.py package/

aws lambda update-function-code \
  --function-name spec-drift-chronometer \
  --zip-file fileb://../deployment_package.zip \
  --region eu-central-1
```

Set the Lambda handler to `main.handler` and configure the API Gateway URL
as `NEXT_PUBLIC_API_URL` in your frontend build.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                     Browser                          │
│   Next.js Dashboard (port 3000)                      │
│   ├── DriftDashboard  — real-time chart + logs       │
│   ├── JustificationGate — Article 14 modal           │
│   └── GovernanceActions — audit buttons              │
└────────────────────┬─────────────────────────────────┘
                     │ HTTP (NEXT_PUBLIC_API_URL)
┌────────────────────▼─────────────────────────────────┐
│   FastAPI Warden Engine (port 8000)                  │
│   ├── GET  /drift          — live drift index        │
│   ├── GET  /gate/status    — gate state              │
│   ├── POST /gate/submit    — invoke Warden Agent     │
│   ├── POST /audit          — generate audit file     │
│   └── GET  /download-audit — serve audit file        │
└────────────────────┬─────────────────────────────────┘
                     │ boto3 (PRODUCTION only)
┌────────────────────▼─────────────────────────────────┐
│   AWS eu-central-1                                   │
│   ├── Amazon Bedrock  — nova-pro-v1:0 reasoning      │
│   └── DynamoDB        — Intent Ledger (optional)     │
└──────────────────────────────────────────────────────┘
```

**Spec Vault (`.kiro/steering/`)** — human-authored intent files the Warden
cross-references for every governance decision:

| File | Purpose |
|------|---------|
| `governance.md` | Warden persona and negotiation protocol |
| `tech.md` | Technology constraints (region, models, runtimes) |
| `product.md` | Vision and strategic pillars |
| `human-intent-specs.md` | Explicit architect declarations (INTENT-001 … INTENT-006) |
| `spec.json` | Machine-readable thresholds and model config |

---

## Environment Variables

See `.env.example` for the full list with descriptions. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `true` | `true` = no AWS needed; `false` = live Bedrock |
| `DRIFT_THRESHOLD` | `0.0075` | Drift value that triggers the Justification Gate |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for the frontend |
| `AWS_REGION` | `eu-central-1` | Must be Frankfurt for data sovereignty |

---

## Tech Stack

- Frontend: Next.js (React) with Tailwind CSS — deployed on Cloudflare Pages
- Backend: FastAPI (Python) with Mangum — deployed on Render
- AI Layer: Amazon Bedrock (Nova Pro for justification analysis, Nova Lite for semantic drift scoring)
- Governance: Spec Vault (`.kiro/steering/`) with real semantic git diff analysis
- Lambda: Dockerfile and Procfile included for AWS Lambda deployment

---

## Sample Audit Trail Output

Every governance decision generates a structured audit file at `.kiro/audit/last_sync.audit`, downloadable directly from the dashboard. This is the Article 12 record-keeping artifact — a tamper-evident, SHA-256-verified log of every human oversight event.

```
╔══════════════════════════════════════════════════════════════╗
║      SPEC-DRIFT CHRONOMETER — SOVEREIGN AUDIT TRAIL         ║
╚══════════════════════════════════════════════════════════════╝

Timestamp:          2026-06-14 15:24:15 UTC
Drift Index:        0.0082
Threshold:          0.0075
Gate Status:        RESOLVED
Spec Hash:          bf40efdc39297d64
Run Hash:           cdfa7ff9a941820f

── GOVERNANCE COMPLIANCE ──────────────────────────────────────
EU AI Act Article 14 (Human Oversight):   VERIFIED
EU AI Act Article 12 (Transparency):      VERIFIED
Sovereign Region:                          eu-central-1 (Frankfurt)
System Integrity:                          100%

── ACTIVE SPECIFICATIONS (.kiro/steering/spec.json) ───────────
Semantic Drift Threshold:  0.0075
Max Latency (ms):          200
Primary Model:             amazon.nova-pro-v1:0
Audit Trail Active:        true

── JUSTIFICATION GATE RECORD ──────────────────────────────────
Decision:         APPROVED
Justification:    Migrating auth layer to OAuth2 to satisfy GDPR Article 7
                  compliance requirements signed off by legal team on 2026-06-10.

══════════════════════════════════════════════════════════════
```

Generated in demo mode. Production deployments replace simulated Bedrock calls with live Amazon Nova Pro reasoning in eu-central-1.

The Warden also enforces quality: a weak justification (`"okay"`) scores 29/100 and is **REJECTED** with a full reasoning trace — proving the gate is not a rubber stamp.

---

## License

Licensed under AGPL-3.0. For commercial licensing or enterprise deployment, contact info@aevoxis.de

---

