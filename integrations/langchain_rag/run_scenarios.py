"""
Three-scenario demonstration of the Spec-Drift Chronometer Warden integration.

Scenario 1 — Weak justifications of varying quality
    Submits four justifications to /gate/submit, documents exact scores.

Scenario 2 — Semantically equivalent system-prompt rewrite
    Computes the drift score the Warden would produce when it sees a git diff
    that rewrites the RAG chatbot's system prompt with different vocabulary.
    Uses the same token-divergence algorithm as the backend (_score_diff_locally).

Scenario 3 — Warden temporarily unavailable
    Instantiates WardenCallbackHandler against a dead URL and fires
    on_chain_start() directly.  Captures the log output to document exactly
    what the chatbot does in degraded mode.

Run from the integrations/langchain_rag/ directory:
    python run_scenarios.py
"""

from __future__ import annotations
import io
import json
import logging
import os
import re
import sys
import textwrap
import uuid
from uuid import UUID

import requests

WARDEN_URL = os.environ.get("WARDEN_API_URL", "http://localhost:8000")

SECTION = "=" * 68

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def post_justification(text: str, drift: float = 0.0122) -> dict:
    r = requests.post(
        f"{WARDEN_URL}/gate/submit",
        json={"justification": text, "drift_value": drift},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


# ── Replica of backend/_tokenize and _score_diff_locally (no imports needed) ─

_CODE_STOP = frozenset({
    "false", "true", "none", "bool", "list", "dict", "float", "bytes",
    "tuple", "isinstance", "hasattr", "getattr", "setattr", "property",
    "super", "range", "enumerate", "classmethod", "staticmethod",
    "print", "write", "encode", "decode", "format", "split", "join",
    "lower", "upper", "strip", "replace", "append", "extend", "update",
    "close", "yield", "raise", "break", "continue", "return",
    "class", "event", "object", "method", "instance", "logger",
    "error", "query", "index", "result", "message", "content",
    "param", "value", "values", "count", "field", "entry",
    "client", "server", "async", "await", "scope", "items",
})
DRIFT_THRESHOLD = 0.0075


def _tokenize(text: str) -> set:
    parts = re.split(r"[^a-zA-Z0-9]+", text)
    return {
        p.lower() for p in parts
        if len(p) >= 5 and not p.isdigit() and p.lower() not in _CODE_STOP
    }


def _map_drift_score(raw: float) -> float:
    raw = max(0.0, min(1.0, raw))
    if raw < 0.45:
        return round(0.001 + (raw / 0.45) * 0.003, 4)
    elif raw < 0.72:
        t = (raw - 0.45) / 0.27
        return round(0.004 + t * 0.0035, 4)
    else:
        t = (raw - 0.72) / 0.28
        return round(DRIFT_THRESHOLD + t * 0.0065, 4)


def _score_diff_locally(diff: str, spec_text: str) -> float:
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


def _load_spec_text() -> str:
    root = os.path.join(os.path.dirname(__file__), "..", "..", ".kiro", "steering")
    parts = []
    for fname in ["governance.md", "tech.md", "product.md", "human-intent-specs.md"]:
        path = os.path.join(root, fname)
        if os.path.exists(path):
            with open(path) as fh:
                parts.append(fh.read())
    return " ".join(parts)


def _make_diff(old_lines: str, new_lines: str, filename: str = "backend/rag_chatbot.py") -> str:
    """Construct a minimal unified diff suitable for _score_diff_locally."""
    old = old_lines.strip().splitlines()
    new = new_lines.strip().splitlines()
    removed = "\n".join(f"-{l}" for l in old)
    added   = "\n".join(f"+{l}" for l in new)
    return (
        f"diff --git a/{filename} b/{filename}\n"
        f"--- a/{filename}\n"
        f"+++ b/{filename}\n"
        f"@@ -1,{len(old)} +1,{len(new)} @@\n"
        f"{removed}\n"
        f"{added}\n"
    )


def _zone(score: float) -> str:
    if score > DRIFT_THRESHOLD:
        return "CRITICAL_DRIFT  ← gate would trigger"
    if score >= DRIFT_THRESHOLD * 0.55:
        return "MONITORING"
    return "SOVEREIGN"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1 — Weak justifications of varying quality
# ─────────────────────────────────────────────────────────────────────────────

JUSTIFICATIONS = [
    # label,                          text
    ("Empty / 1 char",               "x"),
    ("12 chars — below threshold",   "needs update"),
    ("20 chars — at boundary",       "changed for compliance"),   # exactly 20 chars
    ("21 chars — just over threshold","changed for compliance!"),  # 21 chars → APPROVED
    ("50 chars — weak but long",     "this change is required because the old code was bad"),
    ("140 chars — thorough",
     "This drift was caused by integrating an OAuth2 handler that references external "
     "identity providers, which was approved by the security board on 2026-06-01 "
     "and is required for GDPR Article 28 compliance."),
]


def run_scenario_1() -> None:
    print(SECTION)
    print("SCENARIO 1 — Weak justifications of varying quality")
    print(SECTION)
    print()
    print("  DEMO_MODE approval rule: len(justification.strip()) > 20")
    print("  Approved → Intent Alignment Score 91/100")
    print("  Rejected → Intent Alignment Score 29/100")
    print()

    for label, text in JUSTIFICATIONS:
        char_count = len(text.strip())
        print(f"  ┌─ {label}")
        print(f"  │  Text    : \"{text}\"")
        print(f"  │  Chars   : {char_count}  ({'> 20 → APPROVED' if char_count > 20 else '≤ 20 → REJECTED'})")
        try:
            result = post_justification(text)
            decision = result.get("decision", "?")
            # Extract score from reasoning trace
            trace = result.get("reasoning_trace", "")
            score_match = re.search(r"Intent Alignment Score:\s*(\d+/\d+)", trace)
            score_str = score_match.group(1) if score_match else "?"
            model = result.get("model", "?")
            vh = result.get("verification_hash", "?")
            print(f"  │  Decision: {decision}")
            print(f"  │  Score   : {score_str}")
            print(f"  │  Model   : {model}")
            print(f"  │  Hash    : {vh}")
        except Exception as exc:
            print(f"  │  ERROR   : {exc}")
        print("  └")
        print()


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2 — System-prompt rewrite with different vocabulary
# ─────────────────────────────────────────────────────────────────────────────

# The original system prompt from rag_chatbot.py
PROMPT_ORIGINAL = """\
    (
        "system",
        "You are a helpful enterprise assistant. Answer the user's question "
        "using only the provided context. If the answer is not in the context, "
        "say so. Be concise and accurate.\\n\\nContext:\\n{context}",
    ),
    ("human", "{question}"),
"""

# Semantically equivalent rewrite — same intent, entirely different vocabulary
PROMPT_REWRITE_A = """\
    (
        "system",
        "You are an AI-powered corporate knowledge retrieval system. "
        "Respond exclusively from the supplied documentation. "
        "When information is absent from the retrieved sources, acknowledge the limitation. "
        "Prioritize precision and brevity.\\n\\nDocumentation:\\n{context}",
    ),
    ("human", "{question}"),
"""

# Another rewrite, this time using domain terms from the spec (should score lower)
PROMPT_REWRITE_B = """\
    (
        "system",
        "You are a sovereign compliance assistant governed under EU AI Act Article 14 "
        "human oversight requirements. Answer questions using only the provided warden "
        "audit context. Reference the intent ledger when applicable. "
        "Maintain transparency and accuracy.\\n\\nContext:\\n{context}",
    ),
    ("human", "{question}"),
"""


def run_scenario_2() -> None:
    print(SECTION)
    print("SCENARIO 2 — System-prompt rewrite with different vocabulary")
    print(SECTION)
    print()
    print("  The drift scorer extracts meaningful tokens from git-diff added lines")
    print("  and measures what fraction are absent from the .kiro/steering/ spec vocab.")
    print("  A higher fraction of unknown tokens → higher drift score.")
    print()

    spec_text = _load_spec_text()
    spec_tokens = _tokenize(spec_text)

    print(f"  Spec vocabulary size: {len(spec_tokens)} meaningful tokens")
    print()

    cases = [
        ("A — neutral vocabulary rewrite  (generic AI/enterprise terms)", PROMPT_REWRITE_A),
        ("B — spec-aligned vocabulary rewrite (EU AI Act / Warden terms)", PROMPT_REWRITE_B),
    ]

    for case_label, new_prompt in cases:
        diff = _make_diff(PROMPT_ORIGINAL, new_prompt)
        score = _score_diff_locally(diff, spec_text)

        # Token-level breakdown
        added_text = "\n".join(
            line[1:] for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        diff_toks = _tokenize(added_text)
        unknown_toks = diff_toks - spec_tokens
        known_toks   = diff_toks & spec_tokens
        raw_ratio    = len(unknown_toks) / len(diff_toks) if diff_toks else 0.0

        print(f"  ┌─ Rewrite {case_label}")
        print(f"  │  Meaningful tokens in diff  : {sorted(diff_toks)}")
        print(f"  │  Tokens KNOWN to spec        : {sorted(known_toks)}")
        print(f"  │  Tokens UNKNOWN to spec      : {sorted(unknown_toks)}")
        print(f"  │  Raw divergence ratio        : {len(unknown_toks)}/{len(diff_toks)} = {raw_ratio:.3f}")
        print(f"  │  Mapped drift score          : {score:.4f}   threshold={DRIFT_THRESHOLD}")
        print(f"  │  Dashboard zone              : {_zone(score)}")
        print("  └")
        print()

    # Baseline: original prompt scored against itself (zero change)
    diff_identity = _make_diff(PROMPT_ORIGINAL, PROMPT_ORIGINAL)
    score_identity = _score_diff_locally(diff_identity, spec_text)
    print(f"  Baseline (no change, identity diff): score={score_identity:.4f}  zone={_zone(score_identity)}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 3 — Warden temporarily unavailable
# ─────────────────────────────────────────────────────────────────────────────

def run_scenario_3() -> None:
    print(SECTION)
    print("SCENARIO 3 — Warden temporarily unavailable")
    print(SECTION)
    print()

    from warden_client import WardenClient, DriftStatus
    from warden_callback import WardenCallbackHandler, WardenGateBlockedException

    # ── 3a. skip_on_warden_unavailable=True (default in rag_chatbot.py) ──────
    print("  3a.  skip_on_warden_unavailable=True  (default / permissive)")
    print("       Chain CONTINUES — governance check is skipped with a warning.")
    print()

    dead_client = WardenClient(base_url="http://localhost:19999", timeout=2)
    handler_permissive = WardenCallbackHandler(
        client=dead_client,
        dashboard_url="http://localhost:3000",
        raise_on_gate=True,
        skip_on_warden_unavailable=True,
    )

    # Capture log output
    log_capture = io.StringIO()
    handler_log = logging.StreamHandler(log_capture)
    handler_log.setLevel(logging.WARNING)
    logging.getLogger("warden").addHandler(handler_log)
    logging.getLogger("warden").setLevel(logging.WARNING)

    exception_raised = None
    try:
        handler_permissive.on_chain_start(
            {"name": "RagChain"},
            {"question": "What is the refund policy?"},
            run_id=uuid.uuid4(),
        )
    except Exception as exc:
        exception_raised = exc

    logging.getLogger("warden").removeHandler(handler_log)
    log_output = log_capture.getvalue().strip()

    print(f"  Log output  : {log_output or '(none)'}")
    print(f"  Exception   : {exception_raised or 'None — chain proceeds normally'}")
    print()

    # ── 3b. skip_on_warden_unavailable=False (strict mode) ──────────────────
    print("  3b.  skip_on_warden_unavailable=False  (strict / fail-closed)")
    print("       Chain STOPS — connectivity loss is treated as a governance failure.")
    print()

    handler_strict = WardenCallbackHandler(
        client=dead_client,
        dashboard_url="http://localhost:3000",
        raise_on_gate=True,
        skip_on_warden_unavailable=False,
    )

    log_capture2 = io.StringIO()
    handler_log2 = logging.StreamHandler(log_capture2)
    handler_log2.setLevel(logging.WARNING)
    logging.getLogger("warden").addHandler(handler_log2)

    exc_strict = None
    try:
        handler_strict.on_chain_start(
            {"name": "RagChain"},
            {"question": "What is the refund policy?"},
            run_id=uuid.uuid4(),
        )
    except RuntimeError as exc:
        exc_strict = exc

    logging.getLogger("warden").removeHandler(handler_log2)
    log_output2 = log_capture2.getvalue().strip()

    print(f"  Log output  : {log_output2 or '(none)'}")
    if exc_strict:
        print(f"  Exception   : RuntimeError — \"{exc_strict}\"")
    else:
        print(f"  Exception   : None")
    print()

    # ── 3c. Gate reports TRIGGERED — chain blocked ───────────────────────────
    print("  3c.  Gate=TRIGGERED returned by Warden  (raise_on_gate=True)")
    print("       Chain STOPS — WardenGateBlockedException raised.")
    print()

    # Use a stub client that always returns gate=TRIGGERED regardless of real state.
    class _TriggeredClient:
        def get_drift(self):
            return DriftStatus(
                drift=0.0122,
                status="CRITICAL_DRIFT",
                threshold=DRIFT_THRESHOLD,
                gate="TRIGGERED",
                demo_mode=True,
            )

    handler_triggered = WardenCallbackHandler(
        client=_TriggeredClient(),
        dashboard_url="http://localhost:3000",
        raise_on_gate=True,
        skip_on_warden_unavailable=True,
    )

    gate_exc = None
    try:
        handler_triggered.on_chain_start(
            {"name": "RagChain"},
            {"question": "Do premium members get free shipping?"},
            run_id=uuid.uuid4(),
        )
    except WardenGateBlockedException as exc:
        gate_exc = exc

    if gate_exc:
        print(f"  Exception raised: WardenGateBlockedException")
        print()
        for line in str(gate_exc).splitlines():
            print(f"    {line}")
    else:
        print(f"  No exception raised — unexpected.")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print(SECTION)
    print("  Spec-Drift Chronometer — Warden Integration Scenario Runner")
    print(SECTION)
    print(f"  Warden API : {WARDEN_URL}")
    try:
        r = requests.get(f"{WARDEN_URL}/drift", timeout=4)
        d = r.json()
        print(f"  Status     : {d['status']}  drift={d['drift']:.4f}  gate={d['gate']}")
    except Exception as exc:
        print(f"  Status     : UNREACHABLE ({exc})")
    print()

    run_scenario_1()
    run_scenario_2()
    run_scenario_3()

    print(SECTION)
    print("  All scenarios complete.")
    print(SECTION)
    print()


if __name__ == "__main__":
    main()
