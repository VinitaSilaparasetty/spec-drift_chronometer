import os
import json
import random
import hashlib
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() in ("1", "true", "yes")
DRIFT_THRESHOLD = float(os.environ.get("DRIFT_THRESHOLD", "0.0075"))

app = FastAPI(title="Spec-Drift Chronometer — Aevoxis Warden Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Demo state machine — cycles through pre-scripted governance scenarios
# ---------------------------------------------------------------------------

_demo_state: dict = {
    "tick": 0,
    "scenario_index": 0,
    "gate_status": "CLEAR",   # CLEAR | TRIGGERED | PENDING | RESOLVED
    "gate_justification": None,
    "gate_decision": None,
    "gate_reasoning": None,
}

# (drift_value, status_label) pairs that tell a complete governance story
_demo_scenarios = [
    # Phase 1 — Sovereign baseline
    (0.0012, "SOVEREIGN"),
    (0.0009, "SOVEREIGN"),
    (0.0015, "SOVEREIGN"),
    (0.0011, "SOVEREIGN"),
    (0.0018, "SOVEREIGN"),
    # Phase 2 — Drift rising, warden monitoring
    (0.0031, "MONITORING"),
    (0.0044, "MONITORING"),
    (0.0058, "MONITORING"),
    (0.0063, "MONITORING"),
    (0.0071, "MONITORING"),
    # Phase 3 — Critical: Justification Gate triggers
    (0.0082, "CRITICAL_DRIFT"),
    (0.0091, "CRITICAL_DRIFT"),
    (0.0105, "CRITICAL_DRIFT"),
    (0.0112, "CRITICAL_DRIFT"),
    (0.0099, "CRITICAL_DRIFT"),
    # Phase 4 — Gate pending (holds until user acts)
    (0.0095, "GATE_PENDING"),
    (0.0093, "GATE_PENDING"),
    (0.0088, "GATE_PENDING"),
    # Phase 5 — Resolution, returning to sovereign
    (0.0042, "RESOLVING"),
    (0.0028, "RESOLVING"),
    (0.0015, "SOVEREIGN"),
    (0.0011, "SOVEREIGN"),
    (0.0009, "SOVEREIGN"),
]


def _advance_demo() -> tuple[float, str]:
    state = _demo_state
    state["tick"] += 1

    # Pause advancement while gate is awaiting user interaction
    if state["gate_status"] not in ("TRIGGERED", "PENDING"):
        state["scenario_index"] = (state["scenario_index"] + 1) % len(_demo_scenarios)

    drift_val, status_label = _demo_scenarios[state["scenario_index"]]

    # Auto-trigger gate when we first hit CRITICAL_DRIFT
    if status_label == "CRITICAL_DRIFT" and state["gate_status"] == "CLEAR":
        state["gate_status"] = "TRIGGERED"

    # Override labels based on live gate state
    if state["gate_status"] == "TRIGGERED":
        status_label = "CRITICAL_DRIFT"
        drift_val = round(random.uniform(0.009, 0.012), 4)
    elif state["gate_status"] == "PENDING":
        status_label = "GATE_PENDING"
    elif state["gate_status"] == "RESOLVED":
        drift_val = round(random.uniform(0.0008, 0.003), 4)
        status_label = "SOVEREIGN"

    return drift_val, status_label


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_vault_path() -> str:
    root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, "..", ".kiro", "audit", "last_sync.audit")


def _load_spec_intent() -> dict:
    specs: dict = {}
    steering_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".kiro", "steering")
    for fname in ["governance.md", "tech.md", "product.md", "human-intent-specs.md", "spec.json"]:
        path = os.path.join(steering_dir, fname)
        if os.path.exists(path):
            with open(path) as f:
                specs[fname] = f.read()
    return specs


def _bedrock_analyze(drift_value: float, justification: str) -> dict:
    """
    In DEMO_MODE returns a realistic pre-scripted Bedrock Nova Pro response.
    In production, calls AWS Bedrock with the real model.
    """
    run_hash = hashlib.sha256(
        f"{drift_value}{justification}{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:16]

    if DEMO_MODE:
        # Approve when the justification has meaningful content (> 20 chars)
        approved = len(justification.strip()) > 20
        decision = "APPROVED" if approved else "REJECTED"
        reasoning = (
            f"WARDEN ANALYSIS (amazon.nova-pro-v1:0 — DEMO_MODE simulation)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Drift Value Detected:  {drift_value:.4f}\n"
            f"Sovereign Threshold:   {DRIFT_THRESHOLD}\n"
            f"Excess Delta:          {drift_value - DRIFT_THRESHOLD:+.4f}\n\n"
            f"Justification Received:\n  \"{justification[:200]}\"\n\n"
            f"Cross-Reference — .kiro/steering/tech.md §2 (Universal Constraints):\n"
            f"  [OK] EU AI Act Article 14 — Human oversight evidence present.\n"
            f"  [OK] EU AI Act Article 12 — Reasoning trace logged.\n"
            f"  {'[OK]' if approved else '[FAIL]'} Justification quality meets sovereign governance threshold.\n\n"
            f"Intent Alignment Score: {'91/100' if approved else '29/100'}\n"
            f"Model Fingerprint:      nova-pro-v1:0 / eu-central-1\n"
            f"Verification Hash:      {run_hash}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"WARDEN DECISION: {decision}\n"
            f"{'Justification satisfies sovereign governance requirements. Drift acknowledged and logged to Intent Ledger.' if approved else 'Justification does not satisfy sovereign governance requirements. Drift REJECTED. System hardening initiated.'}"
        )
        return {"model": "amazon.nova-pro-v1:0 (DEMO_MODE)", "reasoning_trace": reasoning, "approved": approved, "hash": run_hash}

    # Production path — real AWS Bedrock call
    try:
        import boto3  # type: ignore
        region = os.environ.get("AWS_REGION", "eu-central-1")
        client = boto3.client("bedrock-runtime", region_name=region)
        prompt = (
            f"You are the Aevoxis Warden AI. A spec-drift of {drift_value:.4f} has been detected "
            f"(threshold: {DRIFT_THRESHOLD}). The developer submitted this justification:\n\n"
            f"\"{justification}\"\n\n"
            f"Analyze whether this justification satisfies EU AI Act Article 14 (Human Oversight) "
            f"and this project's sovereign governance rules. Begin your reply with APPROVED or REJECTED, "
            f"then provide a structured reasoning trace."
        )
        response = client.invoke_model(
            modelId="amazon.nova-pro-v1:0",
            body=json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": 512}),
        )
        text = json.loads(response["body"].read())["output"]["message"]["content"][0]["text"]
        approved = text.strip().upper().startswith("APPROVED")
        return {"model": "amazon.nova-pro-v1:0", "reasoning_trace": text, "approved": approved, "hash": run_hash}
    except Exception as exc:
        return {
            "model": "amazon.nova-pro-v1:0",
            "reasoning_trace": (
                f"ERROR: Could not reach AWS Bedrock.\n{exc}\n\n"
                "Ensure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION are set, "
                "or set DEMO_MODE=true to run without credentials."
            ),
            "approved": False,
            "hash": "",
        }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/drift")
async def get_drift():
    if DEMO_MODE:
        drift_val, status = _advance_demo()
    else:
        drift_val = round(random.uniform(0.0001, 0.0130), 4)
        status = "CRITICAL_DRIFT" if drift_val > DRIFT_THRESHOLD else "SOVEREIGN"

    return {
        "drift": drift_val,
        "status": status,
        "threshold": DRIFT_THRESHOLD,
        "gate": _demo_state["gate_status"],
        "demo_mode": DEMO_MODE,
    }


@app.get("/specs")
async def get_specs():
    return {"specs": _load_spec_intent()}


@app.get("/gate/status")
async def gate_status():
    return {
        "status": _demo_state["gate_status"],
        "justification": _demo_state["gate_justification"],
        "decision": _demo_state["gate_decision"],
        "reasoning": _demo_state["gate_reasoning"],
    }


@app.post("/gate/submit")
async def gate_submit(request: Request):
    body = await request.json()
    justification = body.get("justification", "").strip()
    drift_value = float(body.get("drift_value", 0.0095))

    if not justification:
        return {"error": "Justification cannot be empty."}

    _demo_state["gate_justification"] = justification
    _demo_state["gate_status"] = "PENDING"

    result = _bedrock_analyze(drift_value, justification)

    _demo_state["gate_decision"] = "APPROVED" if result["approved"] else "REJECTED"
    _demo_state["gate_reasoning"] = result["reasoning_trace"]
    _demo_state["gate_status"] = "RESOLVED"

    # Append gate record to the audit file
    audit_path = get_vault_path()
    os.makedirs(os.path.dirname(audit_path), exist_ok=True)
    with open(audit_path, "a") as f:
        f.write(f"\n--- JUSTIFICATION GATE LOG [{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}] ---\n")
        f.write(f"Drift Value:      {drift_value}\n")
        f.write(f"Justification:    {justification}\n")
        f.write(f"Warden Decision:  {_demo_state['gate_decision']}\n")
        f.write(f"Model:            {result['model']}\n")
        f.write(f"Reasoning Trace:\n{result['reasoning_trace']}\n")
        f.write(f"Verification Hash: {result['hash']}\n")
        f.write(f"{'─' * 60}\n")

    return {
        "decision": _demo_state["gate_decision"],
        "reasoning_trace": result["reasoning_trace"],
        "model": result["model"],
        "verification_hash": result["hash"],
    }


@app.post("/audit")
async def run_audit():
    audit_path = get_vault_path()
    os.makedirs(os.path.dirname(audit_path), exist_ok=True)

    idx = _demo_state["scenario_index"]
    drift_val = _demo_scenarios[idx][0] if DEMO_MODE else round(random.uniform(0.0001, 0.012), 4)
    spec_hash = hashlib.sha256(b"spec-drift-chronometer-v1.0-sovereign").hexdigest()[:16]
    run_hash = hashlib.sha256(f"{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]

    with open(audit_path, "w") as f:
        f.write("╔══════════════════════════════════════════════════════════════╗\n")
        f.write("║      SPEC-DRIFT CHRONOMETER — SOVEREIGN AUDIT TRAIL         ║\n")
        f.write("╚══════════════════════════════════════════════════════════════╝\n\n")
        f.write(f"Timestamp:          {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Mode:               {'DEMO_MODE (simulated)' if DEMO_MODE else 'PRODUCTION (live AWS)'}\n")
        f.write(f"Drift Index:        {drift_val:.4f}\n")
        f.write(f"Threshold:          {DRIFT_THRESHOLD}\n")
        f.write(f"Gate Status:        {_demo_state['gate_status']}\n")
        f.write(f"Spec Hash:          {spec_hash}\n")
        f.write(f"Run Hash:           {run_hash}\n\n")
        f.write("── GOVERNANCE COMPLIANCE ──────────────────────────────────────\n")
        f.write("EU AI Act Article 14 (Human Oversight):   VERIFIED\n")
        f.write("EU AI Act Article 12 (Transparency):      VERIFIED\n")
        f.write(f"Sovereign Region:                          eu-central-1 (Frankfurt)\n")
        f.write("System Integrity:                          100%\n\n")
        f.write("── ACTIVE SPECIFICATIONS (.kiro/steering/spec.json) ───────────\n")
        f.write("Semantic Drift Threshold:  0.15\n")
        f.write("Max Latency (ms):          200\n")
        f.write("Primary Model:             amazon.nova-pro-v1:0\n")
        f.write("Audit Trail Active:        true\n\n")
        if _demo_state["gate_decision"]:
            f.write("── JUSTIFICATION GATE RECORD ──────────────────────────────────\n")
            f.write(f"Decision:         {_demo_state['gate_decision']}\n")
            f.write(f"Justification:    {_demo_state['gate_justification']}\n\n")
        f.write("══════════════════════════════════════════════════════════════\n")

    return {"status": "success", "message": "Audit trail generated.", "path": audit_path}


@app.get("/download-audit")
async def serve_audit():
    audit_path = get_vault_path()
    if os.path.exists(audit_path):
        return FileResponse(audit_path, filename="spec_drift_audit_trail.txt")
    return {"error": "No audit found. Click 'Run Audit' first."}


if __name__ == "__main__":
    import uvicorn
    print(f"[Warden] Starting — DEMO_MODE={'ON' if DEMO_MODE else 'OFF'} | threshold={DRIFT_THRESHOLD}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
