from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def _drive_until_triggered(max_polls: int = 60) -> dict:
    """Poll /drift until the demo cycle crosses the threshold and the gate fires."""
    for _ in range(max_polls):
        data = client.get("/drift").json()
        if data["gate"] == "TRIGGERED":
            return data
    raise AssertionError("gate never triggered during the demo cycle")


# --- scoring -----------------------------------------------------------------

def test_tokenize_drops_short_tokens_and_code_boilerplate():
    tokens = main._tokenize("def return value: ledger immutable abc")
    assert "ledger" in tokens
    assert "immutable" in tokens
    assert "return" not in tokens  # code stop word
    assert "abc" not in tokens     # shorter than 5 characters


def test_production_scorer_range():
    spec = "ledger immutable verification oversight justification"
    aligned = "+ledger immutable verification oversight justification\n"
    foreign = "+blockchain cryptocurrency tokenomics staking validator\n"
    assert main._score_diff_locally_production("", spec) == 0.0012
    assert main._score_diff_locally_production(aligned, spec) == 0.001
    assert main._score_diff_locally_production(foreign, spec) == 0.014
    assert main._score_diff_locally_production(foreign, spec) > main.DRIFT_THRESHOLD


# --- intent fingerprint ------------------------------------------------------

def test_spec_fingerprint_is_stable_and_detects_any_edit():
    specs = {"tech.md": "region: eu-central-1", "spec.json": "{}"}
    same = dict(reversed(list(specs.items())))
    edited = {**specs, "tech.md": "region: eu-central-1\nnew rule"}
    assert main.spec_fingerprint(specs) == main.spec_fingerprint(same)
    assert main.spec_fingerprint(specs) != main.spec_fingerprint(edited)


# --- API -----------------------------------------------------------------------

def test_drift_endpoint_reports_state_and_finds_intent_files():
    data = client.get("/drift").json()
    assert set(data) >= {"drift", "status", "threshold", "gate", "demo_mode", "spec_vault"}
    assert data["demo_mode"] is True
    assert data["spec_vault"] == "OK"
    assert data["threshold"] == main.DRIFT_THRESHOLD


def test_empty_justification_is_refused():
    resp = client.post("/gate/submit", json={"justification": "   "})
    assert resp.json() == {"error": "Justification cannot be empty."}


def test_gate_blocks_then_resolves_with_logged_decision(fresh_state):
    triggered = _drive_until_triggered()
    assert triggered["drift"] > main.DRIFT_THRESHOLD

    # While waiting for a human, the gate stays triggered.
    assert client.get("/drift").json()["gate"] == "TRIGGERED"

    resp = client.post(
        "/gate/submit",
        json={"justification": "ok", "drift_value": triggered["drift"]},
    ).json()
    assert resp["decision"] == "REJECTED"
    assert resp["model"] == "simulated (DEMO_MODE)"
    assert resp["verification_hash"]
    assert client.get("/gate/status").json()["status"] == "RESOLVED"

    log = fresh_state.read_text(encoding="utf-8")
    assert "JUSTIFICATION GATE LOG" in log
    assert "Warden Decision:  REJECTED" in log


def test_audit_report_records_facts_and_makes_no_compliance_claim(fresh_state):
    triggered = _drive_until_triggered()
    client.post(
        "/gate/submit",
        json={
            "justification": "Approved by the architecture board, ticket GOV-12.",
            "drift_value": triggered["drift"],
        },
    )
    assert client.post("/audit").json()["status"] == "success"

    report = fresh_state.read_text(encoding="utf-8")
    specs = main._load_spec_intent()

    # Facts the system actually holds
    assert main.spec_fingerprint(specs) in report
    assert f"Gate threshold:       {main.DRIFT_THRESHOLD}" in report
    assert "Decision:             APPROVED" in report

    # Earlier gate records survive regenerating the report
    assert "JUSTIFICATION GATE LOG" in report

    # No hard-coded verdicts
    assert "VERIFIED" not in report
    assert "100%" not in report
    assert "Transparency" not in report
    assert "not a compliance certificate" in report


def test_regenerating_audit_keeps_all_gate_records(fresh_state):
    for text in ("ok", "Approved by the architecture board, ticket GOV-12."):
        _drive_until_triggered()
        client.post("/gate/submit", json={"justification": text, "drift_value": 0.01})
        main._rearm_demo_gate()
    client.post("/audit")
    client.post("/audit")
    report = fresh_state.read_text(encoding="utf-8")
    assert report.count("--- JUSTIFICATION GATE LOG") == 2


def test_download_audit_serves_the_report():
    client.post("/audit")
    resp = client.get("/download-audit")
    assert resp.status_code == 200
    assert "AUDIT REPORT" in resp.text
