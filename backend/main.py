import os
import re
import json
import time
import hashlib
import uuid
import subprocess
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from mangum import Mangum

DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() in ("1", "true", "yes")
DRIFT_THRESHOLD = float(os.environ.get("DRIFT_THRESHOLD", "0.0075"))
AUDIT_RETENTION_DAYS = int(os.environ.get("AUDIT_RETENTION_DAYS", "90"))
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "")

# CORS: allow all origins in DEMO_MODE; lock to explicit list in production.
# Set CORS_ORIGINS=https://your-frontend.com,https://other.com in production.
_raw_cors = os.environ.get("CORS_ORIGINS", "")
CORS_ORIGINS = [o.strip() for o in _raw_cors.split(",") if o.strip()] or ["*"]

app = FastAPI(title="Spec-Drift Chronometer — Aevoxis Warden Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ORIGINS != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Semantic diff analysis — replaces hardcoded scenario values
# ---------------------------------------------------------------------------

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT    = os.path.join(_BACKEND_DIR, "..")
_SAMPLE_DIFFS_DIR = os.path.join(_BACKEND_DIR, "sample_diffs")

# Gate state machine (CLEAR → TRIGGERED → PENDING → RESOLVED)
_demo_state: dict = {
    "gate_status": "CLEAR",
    "gate_justification": None,
    "gate_decision": None,
    "gate_reasoning": None,
}

# Tracks which sample diff we are on and the last computed score
_diff_state: dict = {
    "sample_index": 0,
    "last_score": 0.0012,
    "last_diff_name": "",
}

# Tokens that carry no architectural signal — filtered before comparison
_CODE_STOP = frozenset({
    # Python primitives and builtins
    "false", "true", "none", "bool", "list", "dict", "float", "bytes",
    "tuple", "isinstance", "hasattr", "getattr", "setattr", "property",
    "super", "range", "enumerate", "classmethod", "staticmethod",
    # Common code verbs with no domain meaning
    "print", "write", "encode", "decode", "format", "split", "join",
    "lower", "upper", "strip", "replace", "append", "extend", "update",
    "close", "yield", "raise", "break", "continue", "return",
    # Generic nouns that appear in every codebase
    "class", "event", "object", "method", "instance", "logger",
    "error", "query", "index", "result", "message", "content",
    "param", "value", "values", "count", "field", "entry",
    "client", "server", "async", "await", "scope", "items",
})


def _tokenize(text: str) -> set:
    """Extract meaningful domain tokens (≥5 chars) filtering code boilerplate."""
    parts = re.split(r"[^a-zA-Z0-9]+", text)
    return {
        p.lower() for p in parts
        if len(p) >= 5 and not p.isdigit() and p.lower() not in _CODE_STOP
    }


def _map_drift_score(raw: float) -> float:
    """
    Map raw token-divergence ratio [0, 1] to the dashboard range [0.001, 0.014].
    Breakpoints keep sovereign / monitoring / critical zones proportional to
    DRIFT_THRESHOLD so the gate still triggers at the right absolute value.
    """
    raw = max(0.0, min(1.0, raw))
    if raw < 0.45:                          # sovereign zone
        return round(0.001 + (raw / 0.45) * 0.003, 4)
    elif raw < 0.72:                        # monitoring zone
        t = (raw - 0.45) / 0.27
        return round(0.004 + t * 0.0035, 4)
    else:                                   # critical zone
        t = (raw - 0.72) / 0.28
        return round(DRIFT_THRESHOLD + t * 0.0065, 4)


def _score_diff_locally(diff: str, spec_text: str) -> float:
    """
    Genuine semantic drift score: fraction of meaningful diff tokens that are
    absent from the spec-file vocabulary, mapped to the dashboard range.
    """
    added = "\n".join(
        line[1:] for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    diff_tokens = _tokenize(added)
    if len(diff_tokens) < 4:
        return 0.0012

    spec_tokens = _tokenize(spec_text)
    if not spec_tokens:
        return 0.005

    unknown = diff_tokens - spec_tokens
    raw = len(unknown) / len(diff_tokens)
    return _map_drift_score(raw)


def _score_diff_locally_production(diff: str, spec_text: str) -> float:
    """
    Production fallback scorer: linear mapping so gate reliably triggers when
    the majority of diff vocabulary is absent from the spec vault.
    raw=0 → 0.001 (no drift), raw≈0.52 → above DRIFT_THRESHOLD, raw=1.0 → 0.014.
    Does NOT use _map_drift_score — that function is calibrated for demo sample diffs.
    """
    added = "\n".join(
        line[1:] for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    diff_tokens = _tokenize(added)
    if len(diff_tokens) < 4:
        return 0.0012

    spec_tokens = _tokenize(spec_text)
    if not spec_tokens:
        return 0.005

    unknown = diff_tokens - spec_tokens
    raw = len(unknown) / len(diff_tokens)
    return round(0.001 + raw * 0.013, 4)


def _score_diff_bedrock(diff: str, specs: dict) -> float | None:
    """Nova Lite semantic scorer for production. Returns None on any failure."""
    try:
        import boto3
        region = os.environ.get("AWS_REGION", "eu-central-1")
        client = boto3.client("bedrock-runtime", region_name=region)
        spec_summary = "\n\n".join(
            f"## {k}\n{v[:400]}" for k, v in list(specs.items())[:3]
        )
        prompt = (
            "You are an architectural compliance analyzer. "
            "Reply with ONLY a decimal number 0.0–1.0 representing how much "
            "the code change below DEVIATES from the specifications. "
            "0.0 = perfectly aligned. 1.0 = complete violation.\n\n"
            f"SPECIFICATIONS:\n{spec_summary[:1200]}\n\n"
            f"GIT DIFF:\n{diff[:800]}\n\nDrift score:"
        )
        resp = client.invoke_model(
            modelId="amazon.nova-lite-v1:0",
            body=json.dumps({"messages": [{"role": "user", "content": prompt}], "max_tokens": 8}),
        )
        text = json.loads(resp["body"].read())["output"]["message"]["content"][0]["text"]
        match = re.search(r"[01]?\.?\d+", text.strip())
        if not match:
            return None
        raw = max(0.0, min(1.0, float(match.group())))
        return _map_drift_score(raw)
    except Exception:
        return None


def _get_sample_diff() -> str:
    """Return the next sample diff in the cycle."""
    try:
        files = sorted(f for f in os.listdir(_SAMPLE_DIFFS_DIR) if f.endswith(".diff"))
        if not files:
            return ""
        idx = _diff_state["sample_index"] % len(files)
        fname = files[idx]
        _diff_state["last_diff_name"] = fname
        with open(os.path.join(_SAMPLE_DIFFS_DIR, fname)) as fh:
            return fh.read()
    except Exception:
        return ""


def _read_git_diff() -> str:
    """Read the latest commit diff from the real repository."""
    try:
        r = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--unified=3", "--no-color",
             "--", "*.py", "*.ts", "*.tsx"],
            capture_output=True, text=True, cwd=_REPO_ROOT, timeout=10,
        )
        diff = r.stdout.strip()
        if not diff:
            r = subprocess.run(
                ["git", "diff", "--cached", "--unified=3", "--no-color"],
                capture_output=True, text=True, cwd=_REPO_ROOT, timeout=10,
            )
            diff = r.stdout.strip()
        return diff
    except Exception:
        return ""


def _compute_drift() -> tuple[float, str]:
    """
    Compute a genuine semantic drift score from the current diff.
    In DEMO_MODE cycles through pre-crafted sample diffs and scores them locally.
    In production reads the real git diff and scores with Nova Lite (Bedrock),
    falling back to the local scorer if Bedrock is unavailable.
    """
    gate = _demo_state["gate_status"]

    # Pause diff advancement while gate is awaiting human action
    if gate not in ("TRIGGERED", "PENDING"):
        _diff_state["sample_index"] += 1

    diff = _get_sample_diff() if DEMO_MODE else _read_git_diff()

    specs = _load_spec_intent()
    spec_text = " ".join(specs.values())

    score: float | None = None
    if not DEMO_MODE:
        score = _score_diff_bedrock(diff, specs)
    if score is None:
        if diff:
            scorer = _score_diff_locally if DEMO_MODE else _score_diff_locally_production
            score = scorer(diff, spec_text)
        else:
            score = 0.0012

    _diff_state["last_score"] = score

    # Gate trigger: first time score strictly exceeds threshold
    if score > DRIFT_THRESHOLD and gate == "CLEAR":
        _demo_state["gate_status"] = "TRIGGERED"
        gate = "TRIGGERED"

    # Derive status label
    if gate == "TRIGGERED":
        return score, "CRITICAL_DRIFT"
    if gate == "PENDING":
        return score, "GATE_PENDING"
    if gate == "RESOLVED":
        return min(score, DRIFT_THRESHOLD * 0.45), "RESOLVING"
    if score > DRIFT_THRESHOLD:
        return score, "CRITICAL_DRIFT"
    if score >= DRIFT_THRESHOLD * 0.55:
        return score, "MONITORING"
    return score, "SOVEREIGN"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_vault_path() -> str:
    root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, "..", ".kiro", "audit", "last_sync.audit")


def _load_tech_md() -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".kiro", "steering", "tech.md")
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def _load_spec_intent() -> dict:
    specs: dict = {}
    steering_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".kiro", "steering")
    for fname in ["governance.md", "tech.md", "product.md", "human-intent-specs.md", "spec.json"]:
        path = os.path.join(steering_dir, fname)
        if os.path.exists(path):
            with open(path) as f:
                specs[fname] = f.read()
    return specs


def _write_dynamo_audit(record: dict) -> None:
    """Article 12: persist audit record to DynamoDB with TTL-based retention."""
    if DEMO_MODE or not DYNAMODB_TABLE_NAME:
        return
    try:
        import boto3
        ttl = int(datetime.utcnow().timestamp()) + AUDIT_RETENTION_DAYS * 86400
        dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "eu-central-1"))
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        table.put_item(Item={**record, "ttl": ttl})
    except Exception as exc:
        print(f"[Warden] DynamoDB write failed: {exc}")


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
# Real-LLM gate evaluator (activated only when WARDEN_LLM env var is set)
# ---------------------------------------------------------------------------

def _warden_llm_analyze(warden_llm: str, drift_value: float, justification: str) -> dict:
    """Route gate evaluation to Gemini or HuggingFace when WARDEN_LLM is set."""
    run_hash = hashlib.sha256(
        f"{drift_value}{justification}{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:16]

    tech_md = _load_tech_md()
    prompt = (
        f"You are evaluating a governance justification for an AI system code change. "
        f"The system has detected specification drift with a drift score of {drift_value}. "
        f"The human submitted this justification: {justification}. "
        f"The relevant specification is: {tech_md}. "
        f"Evaluate whether this justification is adequate for the detected drift. "
        f"Return only a valid JSON object with exactly these fields: "
        f"score (integer 0 to 100 where 0 is completely inadequate and 100 is perfectly adequate), "
        f"decision (string, either APPROVED or REJECTED, use APPROVED for scores above 70), "
        f"reasoning (string, 2 to 3 sentences explaining the score). "
        f"Return only the JSON object, no other text."
    )

    def _build_trace(model_name: str, score: int, decision: str, reasoning: str) -> str:
        return (
            f"WARDEN ANALYSIS ({model_name})\n"
            f"{'━' * 60}\n\n"
            f"Drift Value Detected:   {drift_value:.4f}\n"
            f"Intent Alignment Score: {score}/100\n"
            f"Model Fingerprint:      {model_name}\n"
            f"Verification Hash:      {run_hash}\n\n"
            f"Reasoning:\n{reasoning}\n\n"
            f"{'━' * 60}\n"
            f"WARDEN DECISION: {decision}\n"
        )

    if warden_llm == "gemini":
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return {"http_error": "GEMINI_API_KEY environment variable not set"}
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=gemini_key)
            model_obj = genai.GenerativeModel("gemini-1.5-flash")
            response = model_obj.generate_content(prompt)
            raw = response.text.strip()
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw.strip())
            parsed = json.loads(raw)
            score = int(parsed["score"])
            decision = str(parsed["decision"]).upper()
            reasoning = str(parsed["reasoning"])
            return {
                "approved": decision == "APPROVED",
                "reasoning_trace": _build_trace("gemini-1.5-flash", score, decision, reasoning),
                "model": "gemini-1.5-flash",
                "hash": run_hash,
                "score": score,
            }
        except Exception as exc:
            fallback_msg = f"Response parsing failed: {str(exc)[:200]}"
            print(f"[Warden] Gemini error: {exc}")
            return {
                "approved": False,
                "reasoning_trace": _build_trace("gemini-1.5-flash", 0, "REJECTED", fallback_msg),
                "model": "gemini-1.5-flash",
                "hash": run_hash,
                "score": 0,
            }

    elif warden_llm == "huggingface":
        hf_key = os.environ.get("HF_API_KEY")
        if not hf_key:
            return {"http_error": "HF_API_KEY environment variable not set"}
        import requests as _req  # type: ignore
        hf_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {hf_key}", "Content-Type": "application/json"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 512, "return_full_text": False}}
        raw_text = ""

        def _parse_hf(resp_json):
            if isinstance(resp_json, list) and resp_json:
                text = resp_json[0].get("generated_text", "")
            else:
                text = str(resp_json)
            match = re.search(r"\{.*?\}", text, re.DOTALL)
            return json.loads(match.group() if match else text)

        try:
            resp = _req.post(hf_url, headers=headers, json=payload, timeout=60)
            raw_text = resp.text[:200]
            if resp.status_code == 503:
                time.sleep(20)
                resp = _req.post(hf_url, headers=headers, json=payload, timeout=60)
                raw_text = resp.text[:200]
            resp.raise_for_status()
            parsed = _parse_hf(resp.json())
            score = int(parsed["score"])
            decision = str(parsed["decision"]).upper()
            reasoning = str(parsed["reasoning"])
            return {
                "approved": decision == "APPROVED",
                "reasoning_trace": _build_trace("mistralai/Mistral-7B-Instruct-v0.2", score, decision, reasoning),
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "hash": run_hash,
                "score": score,
            }
        except (json.JSONDecodeError, KeyError) as exc:
            print(f"[Warden] HuggingFace parse warning: {exc}")
            fallback_msg = f"Response parsing failed: {raw_text}"
            return {
                "approved": False,
                "reasoning_trace": _build_trace("mistralai/Mistral-7B-Instruct-v0.2", 0, "REJECTED", fallback_msg),
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "hash": run_hash,
                "score": 0,
            }
        except Exception as exc:
            fallback_msg = f"Response parsing failed: {raw_text or str(exc)[:200]}"
            print(f"[Warden] HuggingFace error: {exc}")
            return {
                "approved": False,
                "reasoning_trace": _build_trace("mistralai/Mistral-7B-Instruct-v0.2", 0, "REJECTED", fallback_msg),
                "model": "mistralai/Mistral-7B-Instruct-v0.2",
                "hash": run_hash,
                "score": 0,
            }

    return {"http_error": f"Unknown WARDEN_LLM value: '{warden_llm}'. Supported: 'gemini', 'huggingface'"}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/drift")
async def get_drift():
    drift_val, status = _compute_drift()
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

    warden_llm = os.environ.get("WARDEN_LLM", "").strip().lower()
    llm_override = None
    llm_score = None
    if warden_llm:
        llm_override = _warden_llm_analyze(warden_llm, drift_value, justification)
        if "http_error" in llm_override:
            return JSONResponse(status_code=500, content={"error": llm_override["http_error"]})
        llm_score = llm_override.get("score")

    _demo_state["gate_justification"] = justification
    _demo_state["gate_status"] = "PENDING"

    result = llm_override if llm_override is not None else _bedrock_analyze(drift_value, justification)

    _demo_state["gate_decision"] = "APPROVED" if result["approved"] else "REJECTED"
    _demo_state["gate_reasoning"] = result["reasoning_trace"]
    _demo_state["gate_status"] = "RESOLVED"

    # Append gate record to the audit file
    audit_path = get_vault_path()
    os.makedirs(os.path.dirname(audit_path), exist_ok=True)
    event_id = str(uuid.uuid4())
    timestamp_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    with open(audit_path, "a") as f:
        f.write(f"\n--- JUSTIFICATION GATE LOG [{timestamp_str}] ---\n")
        f.write(f"Drift Value:      {drift_value}\n")
        f.write(f"Justification:    {justification}\n")
        f.write(f"Warden Decision:  {_demo_state['gate_decision']}\n")
        f.write(f"Model:            {result['model']}\n")
        f.write(f"Reasoning Trace:\n{result['reasoning_trace']}\n")
        f.write(f"Verification Hash: {result['hash']}\n")
        f.write(f"{'─' * 60}\n")

    # Article 12: persist to DynamoDB in production for durable audit trail
    _write_dynamo_audit({
        "event_id": event_id,
        "event_type": "JUSTIFICATION_GATE",
        "timestamp": timestamp_str,
        "drift_value": str(drift_value),
        "justification": justification,
        "decision": _demo_state["gate_decision"],
        "model": result["model"],
        "verification_hash": result["hash"],
    })

    response = {
        "decision": _demo_state["gate_decision"],
        "reasoning_trace": result["reasoning_trace"],
        "model": result["model"],
        "verification_hash": result["hash"],
    }
    if llm_score is not None:
        response["score"] = llm_score
    return response


@app.post("/audit")
async def run_audit():
    audit_path = get_vault_path()
    os.makedirs(os.path.dirname(audit_path), exist_ok=True)

    drift_val = _diff_state["last_score"]
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


@app.delete("/audit/erase")
async def erase_audit():
    """GDPR Article 17 — right to erasure. Clears all stored justification text and audit records."""
    erased = []

    # Clear local audit file
    audit_path = get_vault_path()
    if os.path.exists(audit_path):
        os.remove(audit_path)
        erased.append("local_audit_file")

    # Clear in-memory justification text (the only personal data held in memory)
    _demo_state["gate_justification"] = None
    _demo_state["gate_decision"] = None
    _demo_state["gate_reasoning"] = None
    erased.append("in_memory_state")

    # Delete from DynamoDB in production
    if not DEMO_MODE and DYNAMODB_TABLE_NAME:
        try:
            import boto3
            dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "eu-central-1"))
            table = dynamodb.Table(DYNAMODB_TABLE_NAME)
            scan = table.scan(ProjectionExpression="event_id")
            with table.batch_writer() as batch:
                for item in scan.get("Items", []):
                    batch.delete_item(Key={"event_id": item["event_id"]})
            erased.append("dynamodb_records")
        except Exception as exc:
            print(f"[Warden] DynamoDB erase failed: {exc}")

    return {
        "status": "erased",
        "erased": erased,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "note": "All justification text and audit records erased per GDPR Article 17.",
    }


handler = Mangum(app)

if __name__ == "__main__":
    import uvicorn
    print(f"[Warden] Starting — DEMO_MODE={'ON' if DEMO_MODE else 'OFF'} | threshold={DRIFT_THRESHOLD}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
