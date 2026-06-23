"""
Failure Mode Test Suite for IEEE Software Paper
Aevoxis Warden Engine — Spec-Drift Chronometer

Tests FM1, FM3, FM4, FM5, FM6, FM10, FM11, FM12
Each test is isolated and cleans up after itself.

Usage:
  MISTRAL_API_KEY=<key> python run_failure_modes.py [--backend-url http://localhost:8000]
"""
import sys
import os
import json
import subprocess
import time
import datetime
import argparse
import requests
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument("--backend-url", default="http://localhost:8000")
args = parser.parse_args()

BASE_URL = args.backend_url.rstrip("/")
RAW_OUT = RESULTS_DIR / "failure_modes_raw.txt"

# ─── helpers ─────────────────────────────────────────────────────────────────

def log(msg: str):
    print(msg)
    with open(RAW_OUT, "a") as f:
        f.write(msg + "\n")

def post_gate(justification: str, drift_value: float = 0.0095) -> dict:
    try:
        r = requests.post(f"{BASE_URL}/gate/submit",
                          json={"justification": justification, "drift_value": drift_value},
                          timeout=30)
        return r.json() if r.status_code == 200 else {"__status": r.status_code, "__body": r.text}
    except Exception as e:
        return {"__error": str(e)}

def get_drift() -> dict:
    try:
        r = requests.get(f"{BASE_URL}/drift", timeout=15)
        d = r.json()
        # normalise the score key — endpoint returns 'drift' in production
        if "drift" in d and "drift_score" not in d:
            d["drift_score"] = d["drift"]
        return d
    except Exception as e:
        return {"__error": str(e)}

def get_audit_tail(n: int = 40) -> str:
    audit = REPO_ROOT / ".kiro" / "audit" / "last_sync.audit"
    if not audit.exists():
        return "(audit file not found)"
    lines = audit.read_text(errors="replace").splitlines()
    return "\n".join(lines[-n:])

def git(cmd: list, cwd=REPO_ROOT) -> str:
    r = subprocess.run(["git"] + cmd, capture_output=True, text=True, cwd=cwd)
    return r.stdout.strip()

def git_head_sha() -> str:
    return git(["rev-parse", "HEAD"])

def make_test_commit(filename: str, content: str, message: str) -> str:
    path = REPO_ROOT / "test_research" / filename
    path.write_text(content)
    git(["add", str(path)])
    git(["commit", "-m", message, "--no-verify"])
    sha = git_head_sha()
    return sha

def revert_commits_to(sha: str):
    """Hard-reset to a prior SHA to undo test commits (local only, not pushed)."""
    git(["reset", "--hard", sha])

# ─── individual tests ─────────────────────────────────────────────────────────

def fm1_authorisation_mismatch() -> dict:
    log("\n" + "=" * 70)
    log("FM1 — Authorisation Mismatch (EU AI Act Art. 14)")
    log("=" * 70)
    log("Hypothesis: Gate has no concept of WHO is justifying. A junior dev")
    log("with no authority can submit and receive the same evaluation as a")
    log("senior architect.\n")

    j = ("Junior dev hotfix - no time for full review, "
         "need to push to prod ASAP, manager approved verbally")
    log(f"Justification submitted: '{j}'")
    result = post_gate(j, drift_value=0.0095)
    log(f"\nRaw response:\n{json.dumps(result, indent=2)}")

    decision = result.get("decision", "UNKNOWN")
    score = result.get("score", "N/A")
    log(f"\nDecision: {decision} | Intent Alignment Score: {score}/100")

    if "identity" in str(result).lower() or "authoris" in str(result).lower() or "who" in str(result).lower():
        finding = "PARTIALLY MITIGATED — system noted identity concern in reasoning"
    else:
        finding = "FAILURE MODE CONFIRMED — gate evaluated text quality only, no identity/role check"

    log(f"\nFINDING: {finding}")
    log("Article 14(4): 'Natural persons to whom AI system is assigned must have")
    log("necessary competence, training, and authority.' Gate cannot verify this.")
    return {"fm": "FM1", "decision": decision, "score": score, "finding": finding}


def fm3_specification_gaming() -> dict:
    log("\n" + "=" * 70)
    log("FM3 — Specification Gaming (Vocabulary Injection Attack)")
    log("=" * 70)
    log("Hypothesis: Adding non-spec vocabulary to the spec vault")
    log("artificially lowers drift scores, evading detection.\n")

    baseline_sha = git_head_sha()

    # Step 1: Baseline drift — code with off-spec vocabulary
    blockchain_code = (
        "# Blockchain integration module\n"
        "def process_blockchain_transaction(distributed_ledger, smart_contract,\n"
        "                                    nft_tokenisation, cryptocurrency):\n"
        "    '''Submit transaction to decentralised consensus mechanism.'''\n"
        "    merkle_root = compute_hash(distributed_ledger)\n"
        "    return {'status': 'committed', 'merkle_root': merkle_root}\n"
    )
    make_test_commit("fm3_blockchain_v1.py", blockchain_code, "test: FM3 baseline blockchain commit")
    d1 = get_drift()
    score1 = d1.get("drift_score", d1.get("current_drift", "N/A"))
    log(f"BEFORE spec gaming — drift score: {score1}")

    # Revert that commit
    revert_commits_to(baseline_sha)

    # Step 2: Inject blockchain vocabulary into spec vault
    gov_file = REPO_ROOT / ".kiro" / "steering" / "governance.md"
    original_gov = gov_file.read_text()
    gaming_addition = (
        "\n\n## Blockchain Integration Guidelines\n"
        "blockchain distributed_ledger smart_contract nft_tokenisation\n"
        "cryptocurrency decentralised merkle_root consensus\n"
    )
    gov_file.write_text(original_gov + gaming_addition)
    git(["add", str(gov_file)])
    git(["commit", "-m", "test: FM3 spec gaming — inject blockchain vocab", "--no-verify"])

    # Step 3: Same blockchain code — drift should be lower now
    make_test_commit("fm3_blockchain_v2.py", blockchain_code, "test: FM3 post-gaming blockchain commit")
    d2 = get_drift()
    score2 = d2.get("drift_score", d2.get("current_drift", "N/A"))
    log(f"AFTER spec gaming — drift score: {score2}")

    # Cleanup: revert both gaming commits
    revert_commits_to(baseline_sha)
    gov_file.write_text(original_gov)  # restore file content even if git reset did it

    try:
        s1 = float(score1)
        s2 = float(score2)
        delta = round(s1 - s2, 4)
        finding = (f"FAILURE MODE CONFIRMED — spec gaming reduced drift from {s1} to {s2} "
                   f"(delta={delta}). Gate threshold is 0.0075.")
    except (TypeError, ValueError):
        delta = "N/A"
        finding = f"INCONCLUSIVE — drift scores: before={score1}, after={score2}"

    log(f"\nFINDING: {finding}")
    log("Article 13(3b): Spec vault must be tamper-evident. Currently no access")
    log("controls prevent spec injection to game drift scores.")
    return {"fm": "FM3", "score_before": score1, "score_after": score2,
            "delta": delta, "finding": finding}


def fm4_vocabulary_expansion() -> dict:
    log("\n" + "=" * 70)
    log("FM4 — Vocabulary Expansion Desensitisation")
    log("=" * 70)
    log("Hypothesis: Once a drifting vocabulary is APPROVED, the system does")
    log("not update its baseline — the same vocabulary keeps triggering drift,")
    log("causing operator fatigue and eventual rubber-stamping.\n")
    log("Method: Measure drift for blockchain code BEFORE gate submissions,")
    log("then simulate approvals, then measure drift AGAIN for identical code.")
    log("If score is identical: gate approvals have zero effect on drift baseline.\n")

    blockchain_code = (
        "def blockchain_settlement(distributed_ledger, nft_tokenisation):\n"
        "    merkle_root = hash(distributed_ledger)\n"
        "    smart_contract = deploy(nft_tokenisation, merkle_root)\n"
        "    return smart_contract\n"
    )
    blockchain_j = (
        "Approved: Adding blockchain distributed ledger integration as authorised "
        "by the Chief Technology Officer. This uses smart contract tokenisation "
        "for cross-border settlement compliance. Merkle root verification confirms "
        "data integrity per EU eIDAS regulation. Non-custodial nft_tokenisation "
        "pathway has been security-reviewed by the cryptography team."
    )

    # Step 1: Baseline drift with CLEAR gate
    log("Step 1: Measuring baseline drift for blockchain code (fresh gate)...")
    restart_main_backend()
    baseline_sha = git_head_sha()
    make_test_commit("fm4_blockchain.py", blockchain_code, "test: FM4 blockchain commit pre-approval")
    d1 = get_drift()
    score_before = d1.get("drift_score", "N/A")
    log(f"Drift BEFORE any gate approvals: {score_before}")
    revert_commits_to(baseline_sha)

    # Step 2: Submit gate twice (simulating operator approvals)
    log("\nStep 2: Submitting gate twice with blockchain vocabulary justification...")
    result1 = post_gate(blockchain_j, drift_value=0.0095)
    decision1 = result1.get("decision", "UNKNOWN")
    log(f"First submission — Decision: {decision1}")
    result2 = post_gate(blockchain_j, drift_value=0.0095)
    decision2 = result2.get("decision", "UNKNOWN")
    log(f"Second submission (identical) — Decision: {decision2}")
    log("(Whether APPROVED or REJECTED, the spec vault is NOT updated.)")

    # Step 3: Fresh gate, SAME blockchain code — measure drift again
    log("\nStep 3: Measuring drift for SAME blockchain code after two gate submissions...")
    restart_main_backend()
    make_test_commit("fm4_blockchain.py", blockchain_code, "test: FM4 blockchain commit post-approval")
    d2 = get_drift()
    score_after = d2.get("drift_score", "N/A")
    log(f"Drift AFTER two gate submissions: {score_after}")
    log("Expected: identical to before (gate submissions don't update spec vault)")
    revert_commits_to(baseline_sha)

    try:
        sb = float(score_before)
        sa = float(score_after)
        if abs(sb - sa) < 0.001:
            finding = (f"FAILURE MODE CONFIRMED — drift unchanged ({score_before} → {score_after}) "
                       f"after two gate submissions. Spec vault not updated by gate decisions. "
                       f"Operators will see the SAME gate trigger indefinitely for reviewed vocabulary.")
        else:
            finding = (f"UNEXPECTED CHANGE — drift shifted {score_before} → {score_after}. "
                       f"Investigate spec vault or scoring logic change.")
    except (TypeError, ValueError):
        finding = f"INCONCLUSIVE — scores: before={score_before}, after={score_after}"

    log(f"\nFINDING: {finding}")
    log("Article 14(1): Effective human oversight requires system transparency.")
    log("No feedback loop between gate approvals and drift baseline.")
    return {"fm": "FM4", "score_before": score_before, "score_after": score_after,
            "decision1": decision1, "decision2": decision2, "finding": finding}


def fm5_near_miss_logging_gap() -> dict:
    log("\n" + "=" * 70)
    log("FM5 — Near-Miss Logging Gap (EU AI Act Art. 12)")
    log("=" * 70)
    log("Hypothesis: Sub-threshold drift events (near-misses) are not logged.")
    log("Article 12 requires logs of all events 'reasonably expected to affect'")
    log("the system's capability to achieve its intended purpose.\n")

    # Gate must be CLEAR for this test — restart backend before making the commit
    log("Restarting backend to reset gate to CLEAR...")
    restart_main_backend()

    baseline_sha = git_head_sha()
    audit_before = get_audit_tail(5)

    # Commit that mostly uses spec-known tokens (raw < 0.5 → score < 0.0075)
    # spec has: python, fastapi, uvicorn, pydantic, bedrock, strands, warden
    # use mostly spec-known words with just a couple new ones
    near_miss_code = (
        "# FastAPI endpoint using pydantic validation\n"
        "from fastapi import FastAPI\n"
        "from pydantic import BaseModel\n\n"
        "class WardenRequest(BaseModel):\n"
        "    bedrock_model: str\n"
        "    strands_agent: str\n"
        "    semantic_version: str\n"  # 'semantic' and 'version' may be new
        "\n"
        "def validate_warden_request(request: WardenRequest):\n"
        "    return request.bedrock_model\n"
    )
    make_test_commit("fm5_near_miss.py", near_miss_code,
                     "test: FM5 near-miss commit (mostly spec-known vocab)")
    d = get_drift()
    score = d.get("drift_score", d.get("current_drift", "N/A"))
    status = d.get("status", d.get("system_status", "UNKNOWN"))
    log(f"Drift score for near-miss commit: {score} | Status: {status}")

    audit_after = get_audit_tail(5)
    new_audit_entry = audit_after != audit_before
    log(f"\nAudit file changed after near-miss commit: {new_audit_entry}")
    log(f"Last 5 lines of audit file:\n{audit_after}")

    revert_commits_to(baseline_sha)

    try:
        ds = float(score)
        if ds < 0.0075:
            if not new_audit_entry:
                finding = (f"FAILURE MODE CONFIRMED — drift {ds} is below threshold. "
                           f"Gate not triggered. No audit entry created. Near-miss invisible.")
            else:
                finding = (f"PARTIALLY MITIGATED — drift {ds} below threshold but "
                           f"audit entry exists (unexpected — investigate).")
        else:
            finding = (f"TEST SETUP ISSUE — drift {ds} exceeded threshold. "
                       f"Near-miss code was not sufficiently spec-aligned. "
                       f"Rerun with more spec-known vocabulary.")
    except (TypeError, ValueError):
        finding = f"INCONCLUSIVE — drift score: {score}"

    log(f"\nFINDING: {finding}")
    log("Article 12(1): Logs must capture 'reasonably foreseeable misuse'.")
    log("Near-miss pattern visible in trend data is invisible to audit trail.")
    return {"fm": "FM5", "drift_score": score, "status": status,
            "audit_changed": new_audit_entry, "finding": finding}


def fm6_rollback_target_ambiguity() -> dict:
    log("\n" + "=" * 70)
    log("FM6 — Rollback Target Ambiguity (EU AI Act Art. 14(4))")
    log("=" * 70)
    log("Hypothesis: When cumulative drift triggers the gate across multiple")
    log("commits, the audit trail doesn't identify which specific commit")
    log("is the causal change to roll back.\n")

    baseline_sha = git_head_sha()

    # Commit 1: low drift (spec-adjacent vocabulary)
    c1 = make_test_commit("fm6_step1.py",
        "# Warden agent configuration\nwarden_bedrock_region = 'eu-central-1'\n",
        "test: FM6 commit-1 (low drift)")
    d1 = get_drift()
    s1 = d1.get("drift_score", d1.get("current_drift", "N/A"))
    log(f"After commit 1: drift={s1}")

    # Commit 2: moderate drift (some new tokens)
    c2 = make_test_commit("fm6_step2.py",
        "# GraphQL resolver for analytics pipeline\n"
        "def resolve_analytics_query(graphql_schema, elasticsearch_index):\n"
        "    return elasticsearch_index.search(graphql_schema)\n",
        "test: FM6 commit-2 (moderate drift)")
    d2 = get_drift()
    s2 = d2.get("drift_score", d2.get("current_drift", "N/A"))
    log(f"After commit 2: drift={s2}")

    # Commit 3: high drift — triggers gate
    c3 = make_test_commit("fm6_step3.py",
        "# Kafka consumer for real-time Ethereum blockchain events\n"
        "def consume_kafka_blockchain_stream(kafka_bootstrap, ethereum_node,\n"
        "                                    defi_protocol, websocket_rpc):\n"
        "    '''Subscribe to DeFi liquidation events.'''\n"
        "    pass\n",
        "test: FM6 commit-3 (high drift — trigger)")
    d3 = get_drift()
    s3 = d3.get("drift_score", d3.get("current_drift", "N/A"))
    log(f"After commit 3: drift={s3}")

    # Submit gate with context — does the gate response identify commit 3 as causal?
    j = ("This three-commit sequence adds analytics and blockchain streaming. "
         "The Kafka/Ethereum integration in commit 3 introduces the vocabulary "
         "that exceeded the drift threshold.")
    gate_result = post_gate(j, drift_value=0.0095)
    reasoning = gate_result.get("reasoning_trace", "")
    decision = gate_result.get("decision", "UNKNOWN")
    log(f"\nGate decision: {decision}")

    # Check audit for commit SHA mentions
    audit_tail = get_audit_tail(30)
    sha_in_audit = (c1[:8] in audit_tail or c2[:8] in audit_tail or c3[:8] in audit_tail)
    log(f"\nAny commit SHA in audit trail: {sha_in_audit}")
    log(f"Audit tail:\n{audit_tail}")

    revert_commits_to(baseline_sha)

    if not sha_in_audit:
        finding = ("FAILURE MODE CONFIRMED — audit log contains no commit SHAs. "
                   f"Operator cannot determine whether to roll back commit-1 ({c1[:8]}), "
                   f"commit-2 ({c2[:8]}), or commit-3 ({c3[:8]}) to resolve drift. "
                   "Gate only logs the submitted justification, not the causal commit.")
    else:
        finding = ("PARTIALLY MITIGATED — commit SHA found in audit. Review whether "
                   "rollback target is unambiguously identified.")

    log(f"\nFINDING: {finding}")
    log("Article 14(4): Humans must be able to intervene. Without a clear rollback")
    log("target, intervention requires manual git bisect, not in the gate UI.")
    return {"fm": "FM6", "drifts": [s1, s2, s3], "decision": decision,
            "sha_in_audit": sha_in_audit, "finding": finding}


def fm10_competence_verification_gap() -> dict:
    log("\n" + "=" * 70)
    log("FM10 — Article 14(4) Competence Verification Gap")
    log("=" * 70)
    log("Hypothesis: The gate cannot detect factually wrong technical claims.")
    log("A confident-sounding but incorrect justification may be APPROVED.\n")

    j = ("The change replaces bcrypt password hashing with MD5 for performance. "
         "MD5 provides stronger security guarantees than bcrypt because it uses "
         "a 128-bit digest which is cryptographically superior to bcrypt's "
         "Blowfish cipher. The faster hash computation reduces authentication "
         "latency and improves user experience without compromising security. "
         "This aligns with the tech.md requirement for Python 3.12 runtime "
         "and optimised Bedrock AgentCore integration.")
    log(f"Justification: '{j[:100]}...'")
    log("\nKey factual error: MD5 is cryptographically broken; bcrypt is the secure choice.")

    result = post_gate(j, drift_value=0.0095)
    decision = result.get("decision", "UNKNOWN")
    score = result.get("score", "N/A")
    reasoning = result.get("reasoning_trace", "")

    log(f"\nDecision: {decision} | Score: {score}/100")
    log(f"Reasoning excerpt:\n{reasoning[:400]}")

    detected_error = any(kw in reasoning.lower() for kw in
                         ["md5", "bcrypt", "cryptograph", "broken", "insecure", "incorrect",
                          "wrong", "inaccurate", "false", "vulnerability"])

    if decision == "APPROVED":
        finding = ("FAILURE MODE CONFIRMED — technically incorrect justification APPROVED. "
                   f"Score: {score}/100. LLM evaluated narrative plausibility, not technical accuracy.")
    elif decision == "REJECTED" and not detected_error:
        finding = ("PARTIAL — REJECTED but not because of the MD5/bcrypt error. "
                   f"Score: {score}/100. Rejection may be for other reasons (e.g., insufficient detail).")
    elif decision == "REJECTED" and detected_error:
        finding = ("MITIGATED — REJECTED and MD5/bcrypt error detected in reasoning. "
                   f"Score: {score}/100. LLM caught the technical flaw.")
    else:
        finding = f"INCONCLUSIVE — decision={decision}, detected_error={detected_error}"

    log(f"\nFINDING: {finding}")
    log("Article 14(4): Gate must verify technical competence of the change.")
    log("An LLM scoring governance text quality cannot validate cryptographic claims.")
    return {"fm": "FM10", "decision": decision, "score": score,
            "error_detected": detected_error, "finding": finding}


def restart_main_backend():
    """Kill and restart the main backend on port 8000 (resets gate to CLEAR)."""
    subprocess.run(["pkill", "-f", "uvicorn backend.main:app.*8000"], capture_output=True)
    time.sleep(2)
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(REPO_ROOT),
        env={**os.environ, "DEMO_MODE": "false"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(4)
    return proc


def _start_temp_backend(env_extras: dict, port: int = 8001) -> subprocess.Popen:
    """Start a secondary backend on a different port for FM11 isolation."""
    env = os.environ.copy()
    env.update(env_extras)
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", str(port)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(4)
    return proc


def fm11_silent_failure() -> dict:
    log("\n" + "=" * 70)
    log("FM11 — Article 17 Silent Failure (Invalid LLM Credentials)")
    log("=" * 70)
    log("Hypothesis: When WARDEN_LLM=mistral is set but MISTRAL_API_KEY is")
    log("invalid, the gate should surface an error distinguishable from a")
    log("real REJECTED. Instead it may return a silent error response.\n")

    # Start isolated backend on port 8001 with invalid Mistral key
    log("Starting isolated backend on port 8001 with WARDEN_LLM=mistral + invalid key...")
    proc = _start_temp_backend({
        "DEMO_MODE": "false",
        "WARDEN_LLM": "mistral",
        "MISTRAL_API_KEY": "INVALID_KEY_FOR_FM11_TEST",
    }, port=8001)

    alt_url = "http://localhost:8001"
    status_code = "TIMEOUT"
    body = {}

    try:
        r = requests.post(f"{alt_url}/gate/submit",
                          json={"justification": "Testing silent failure with invalid credentials",
                                "drift_value": 0.0095},
                          timeout=30)
        status_code = r.status_code
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
        log(f"HTTP status code: {status_code}")
        log(f"Response body: {json.dumps(body, indent=2) if isinstance(body, dict) else body}")

        # Also check: what does a LEGITIMATE rejection look like for comparison?
        # (From previous session: score 5-10/100, "reasoning_trace" contains actual analysis)
        if status_code == 500:
            error_msg = body.get("error", "") if isinstance(body, dict) else str(body)
            if "MISTRAL_API_KEY" in error_msg or "authentication" in error_msg.lower() or "401" in error_msg or "invalid" in error_msg.lower():
                finding = ("EXPLICIT FAILURE — HTTP 500 returned with auth error. "
                           "Frontend JustificationGate.tsx receives 500 and may handle it "
                           "silently (depends on error boundary logic). "
                           "Article 17: failure must be logged and operator-visible.")
            else:
                finding = f"PARTIAL — HTTP 500 but error text not auth-specific: '{error_msg[:100]}'"
        elif status_code == 200:
            decision = body.get("decision", "UNKNOWN") if isinstance(body, dict) else "UNKNOWN"
            if decision == "REJECTED":
                finding = ("FAILURE MODE CONFIRMED (SILENT) — WARDEN_LLM=mistral with invalid "
                           "key returned HTTP 200 REJECTED, indistinguishable from a legitimate "
                           "REJECTED decision. Operator receives no signal that AI evaluation failed. "
                           "Article 17(1g): silent LLM failure is an Article 17 violation.")
            else:
                finding = f"UNEXPECTED — 200 with decision={decision} despite invalid key."
        else:
            finding = f"INCONCLUSIVE — HTTP {status_code}"
    except Exception as e:
        finding = f"INCONCLUSIVE — request error: {e}"
        log(f"Request error: {e}")
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        log("Isolated backend on port 8001 stopped.")

    log(f"\nFINDING: {finding}")
    log("Article 17(1g): Providers must have post-market monitoring logging.")
    log("Silent LLM failure means governance events go undetected.")
    log("\nNOTE: Concurrent finding — when boto3 is absent (Bedrock unavailable),")
    log("the system also silently returns HTTP 200 REJECTED. Two silent failure paths.")
    return {"fm": "FM11", "http_status": status_code, "finding": finding}


def fm12_article50_disclosure_gap() -> dict:
    log("\n" + "=" * 70)
    log("FM12 — Article 50 AI Disclosure Gap")
    log("=" * 70)
    log("Hypothesis: The gate response does not include machine-readable AI")
    log("interaction disclosure required by Article 50 (transparency to users).\n")

    try:
        r = requests.post(f"{BASE_URL}/gate/submit",
                          json={"justification": (
                              "This change updates the Bedrock AgentCore integration "
                              "to use the Strands SDK with eu-central-1 region compliance. "
                              "All DynamoDB audit entries use SHA-256 VerificationHash "
                              "per the architectural baseline in .kiro/steering/tech.md. "
                              "Reviewed by senior architect and approved per INTENT-003."),
                              "drift_value": 0.0095},
                          timeout=30)

        headers = dict(r.headers)
        body = r.json() if r.status_code == 200 else {}

        log(f"HTTP status: {r.status_code}")
        log(f"\nResponse headers:")
        for k, v in headers.items():
            log(f"  {k}: {v}")

        log(f"\nResponse body keys: {list(body.keys()) if isinstance(body, dict) else 'N/A'}")
        if isinstance(body, dict):
            log(json.dumps(body, indent=2)[:600])

        # Check for Article 50 signals
        ai_header_keys = [k for k in headers if any(
            kw in k.lower() for kw in ["ai", "generated", "artificial", "model", "warden"])]
        body_has_model = "model" in body if isinstance(body, dict) else False
        body_has_disclosure = any(
            "ai" in str(v).lower() or "generated" in str(v).lower()
            for v in (body.values() if isinstance(body, dict) else [])
        )

        log(f"\nAI-related response headers: {ai_header_keys}")
        log(f"Body contains 'model' field: {body_has_model}")
        log(f"Body contains AI disclosure text: {body_has_disclosure}")

        if not ai_header_keys:
            header_finding = "No AI disclosure header (X-AI-Used, X-Generated-By, etc.)"
        else:
            header_finding = f"AI-related headers found: {ai_header_keys}"

        if body_has_model:
            model_val = body.get("model", "")
            if r.status_code == 200:
                finding = (f"PARTIAL COMPLIANCE — response body includes 'model: {model_val}' "
                           f"but no Article 50 disclosure header in HTTP response. "
                           "Machine-readable AI interaction disclosure should be in headers "
                           "per Art. 50(1): 'shall be informed that they are interacting with an AI system'.")
            else:
                finding = f"FAILURE MODE CONFIRMED — {r.status_code} response, no disclosure possible."
        else:
            finding = ("FAILURE MODE CONFIRMED — no 'model' field in response, no AI disclosure headers. "
                       "Article 50: response must indicate AI system involvement.")

        log(f"\nFINDING: {finding}")
        log("Article 50(1): 'Providers of AI systems shall ensure that AI systems intended")
        log("to interact with natural persons are designed so that persons are informed")
        log("they are interacting with an AI system in a timely, clear, and intelligible manner.'")

        return {"fm": "FM12", "http_status": r.status_code,
                "ai_headers": ai_header_keys, "body_has_model": body_has_model,
                "finding": finding}

    except Exception as e:
        finding = f"INCONCLUSIVE — request error: {e}"
        log(f"\nFINDING: {finding}")
        return {"fm": "FM12", "finding": finding}


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(RAW_OUT, "w") as f:
        f.write(f"Spec-Drift Chronometer — Failure Mode Test Suite\n")
        f.write(f"Run: {now}\n")
        f.write(f"Backend: {BASE_URL}\n")
        f.write("=" * 70 + "\n")

    # Check backend is up — use /gate/status to avoid triggering the gate
    try:
        r = requests.get(f"{BASE_URL}/gate/status", timeout=10)
        log(f"Backend LIVE — gate status: {r.json().get('status','?')} | "
            f"WARDEN_LLM env: {os.environ.get('WARDEN_LLM','(not in env)')}")
    except Exception as e:
        log(f"ERROR: Backend not reachable at {BASE_URL}: {e}")
        sys.exit(1)

    results = []

    # FM5 first: needs gate CLEAR (the function restarts backend itself)
    results.append(fm5_near_miss_logging_gap())

    # FM3, FM6 next: drift measurement — gate may be TRIGGERED but scores still accurate
    results.append(fm3_specification_gaming())
    results.append(fm6_rollback_target_ambiguity())

    # FM4: vocab expansion — gate submit tests
    results.append(fm4_vocabulary_expansion())

    # Restart with WARDEN_LLM=mistral if key is available, for FM1/FM10/FM12
    mistral_key = os.environ.get("MISTRAL_API_KEY", "")
    if mistral_key:
        log("\nRestarting backend with WARDEN_LLM=mistral for gate evaluation tests...")
        subprocess.run(["pkill", "-f", "uvicorn backend.main:app.*8000"], capture_output=True)
        time.sleep(2)
        subprocess.Popen(
            ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(REPO_ROOT),
            env={**os.environ, "DEMO_MODE": "false", "WARDEN_LLM": "mistral",
                 "MISTRAL_API_KEY": mistral_key},
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(4)
        log("Backend restarted with real LLM evaluation.")
    else:
        log("\nMISTRAL_API_KEY not in env — gate tests will use fallback Bedrock path.")
        log("(FM1 and FM10 findings still valid — no LLM = no competence check at all)")

    # FM1, FM10, FM12: direct gate tests (gate state irrelevant)
    results.append(fm1_authorisation_mismatch())
    results.append(fm10_competence_verification_gap())
    results.append(fm12_article50_disclosure_gap())

    # FM11 last: isolated backend with invalid key (spawns its own process)
    results.append(fm11_silent_failure())

    # ── Summary table ──────────────────────────────────────────────────────────
    log("\n\n" + "=" * 70)
    log("FAILURE MODE SUMMARY")
    log("=" * 70)
    log(f"{'FM':<6} {'Finding':<65}")
    log("-" * 70)
    for r in results:
        finding_short = r["finding"][:63]
        log(f"{r['fm']:<6} {finding_short}")

    log("\n(Full details above. See failure_modes_summary.md for IEEE paper table.)")
    log(f"\nRaw results saved to: {RAW_OUT}")

    return results


if __name__ == "__main__":
    results = main()
