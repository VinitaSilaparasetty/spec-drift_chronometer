import os
import sys

import pytest

# The backend is a single module in backend/; make it importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# Tests run against the demo configuration: no cloud account, no API keys.
os.environ["DEMO_MODE"] = "true"
os.environ.pop("WARDEN_LLM", None)

import main  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_state(tmp_path, monkeypatch):
    """Reset the in-memory gate and write audit files to a temp directory."""
    monkeypatch.delenv("WARDEN_LLM", raising=False)
    audit_file = tmp_path / "audit" / "last_sync.audit"
    monkeypatch.setattr(main, "get_vault_path", lambda: str(audit_file))
    main._rearm_demo_gate()
    main._diff_state["last_score"] = 0.0012
    yield audit_file
    main._rearm_demo_gate()
