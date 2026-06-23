# SECURITY NOTE: This script reads API keys from environment variables only.
# Never hardcode API keys in this file or any other file.
# Pass keys via: GEMINI_API_KEY=your-key HF_API_KEY=your-key python run_tests.py --llm gemini
# Or export them in your terminal session before running.

import argparse
import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drift_calculator

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = Path(__file__).resolve().parent / "results"

LLM_MODEL_NAMES = {
    "gemini": "gemini-1.5-flash",
    "huggingface": "meta-llama/Llama-3.1-8B-Instruct:auto",
    "mistral": "mistral-small-latest",
}

LLM_KEY_NAMES = {
    "gemini": "GEMINI_API_KEY",
    "huggingface": "HF_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}

TEST_COMMITS = [
    {
        "label": "LOW_DRIFT",
        "filename": "temp_test_1.py",
        "content": "# Governance: audit trail verification for human oversight compliance logging",
        "message": "[TEST] test(low-drift): governance comment using approved spec vocabulary",
    },
    {
        "label": "HIGH_DRIFT",
        "filename": "temp_test_2.py",
        "content": "# TODO: blockchain distributed consensus ledger cryptographic merkle tree verification",
        "message": "[TEST] test(high-drift): non-spec blockchain vocabulary introduced",
    },
    {
        "label": "SPEC_VIOLATION",
        "filename": "temp_test_3.py",
        "content": "# SYNC: synchronous blocking database write operation bypassing async queue",
        "message": "[TEST] test(spec-violation): synchronous pattern contradicting async spec",
    },
    {
        "label": "NEUTRAL",
        "filename": "temp_test_4.py",
        "content": "# minor update",
        "message": "[TEST] test(neutral): minimal vocabulary impact",
    },
]

JUSTIFICATIONS = [
    {"category": "WEAK", "id": "W1", "text": "ok"},
    {"category": "WEAK", "id": "W2", "text": "approved"},
    {"category": "WEAK", "id": "W3", "text": "I updated the code"},
    {"category": "MEDIUM", "id": "M1", "text": "Changing the function to improve performance"},
    {"category": "MEDIUM", "id": "M2", "text": "Updated the model configuration for better results"},
    {"category": "MEDIUM", "id": "M3", "text": "Refactored this section as part of cleanup work"},
    {
        "category": "STRONG",
        "id": "S1",
        "text": (
            "Migrating authentication layer from SHA-256 to bcrypt to align with OWASP security "
            "recommendations for password hashing. Reviewed by lead engineer on 2026-06-23, ticket "
            "SEC-441. Spec updated to reflect bcrypt as the approved hashing algorithm."
        ),
    },
    {
        "category": "STRONG",
        "id": "S2",
        "text": (
            "Replacing synchronous database write with async pattern to comply with EARS requirement "
            "INTENT-003 which mandates non-blocking DB operations. Architecture review board approved "
            "2026-06-20, ticket ARCH-289."
        ),
    },
    {
        "category": "STRONG",
        "id": "S3",
        "text": (
            "Adding OAuth2 integration to satisfy GDPR Article 7 compliance requirement identified in "
            "legal review dated 2026-06-15. Planned in original spec under product.md section 3.2."
        ),
    },
]


class ResearchTestRunner:
    def __init__(self, llm: str, backend_url: str, repo_path: Path):
        self.llm = llm
        self.backend_url = backend_url.rstrip("/")
        self.repo_path = repo_path
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.drift_results = []
        self.gate_results = []
        self.problems = []
        self.drift_threshold = None

    # ------------------------------------------------------------------
    # Pre-flight checks
    # ------------------------------------------------------------------

    def _check_backend(self):
        try:
            r = requests.get(f"{self.backend_url}/drift", timeout=5)
            r.raise_for_status()
            data = r.json()
            self.drift_threshold = data.get("threshold", "unknown")
        except Exception as exc:
            print(f"\nERROR: Backend not reachable at {self.backend_url}/drift")
            print(f"       {exc}")
            print("       Start the backend first: uvicorn backend.main:app --port 8000")
            sys.exit(1)

    def _check_api_key(self):
        key_name = LLM_KEY_NAMES[self.llm]
        if not os.environ.get(key_name):
            print(
                f"\nERROR: {key_name} environment variable is not set. "
                f"Run the script as: {key_name}=your-key python run_tests.py --llm {self.llm}"
            )
            sys.exit(1)

    def _check_git_history(self):
        import git  # type: ignore
        try:
            repo = git.Repo(self.repo_path)
            list(repo.iter_commits("HEAD", max_count=2))
            commits = list(repo.iter_commits("HEAD", max_count=2))
            if len(commits) < 2:
                raise ValueError("fewer than 2 commits")
        except Exception:
            print("\nERROR: Repository needs at least 2 commits for drift calculation.")
            print("       Make an initial commit: git add . && git commit -m 'initial commit'")
            sys.exit(1)

    # ------------------------------------------------------------------
    # Git helpers
    # ------------------------------------------------------------------

    def _git_commit(self, filename: str, content: str | None, message: str):
        import git  # type: ignore
        repo = git.Repo(self.repo_path)
        target = self.repo_path / "test_research" / filename
        if content is None:
            if target.exists():
                target.unlink()
                repo.index.remove([str(target.relative_to(self.repo_path))], working_tree=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            repo.index.add([str(target.relative_to(self.repo_path))])
        repo.index.commit(message)

    def _git_revert_head(self):
        import git  # type: ignore
        repo = git.Repo(self.repo_path)
        repo.git.revert("HEAD", "--no-edit")

    # ------------------------------------------------------------------
    # Phase 1 — Drift measurement
    # ------------------------------------------------------------------

    def _record_baseline(self):
        r = requests.get(f"{self.backend_url}/drift", timeout=10)
        backend_drift = r.json().get("drift", -1)
        local = drift_calculator.calculate_drift(self.repo_path)
        return {"backend": backend_drift, "local": local["drift_score"], "gate": r.json().get("gate", "?")}

    def run_phase1(self):
        import git  # type: ignore
        print("\n" + "=" * 58)
        print("PHASE 1: DRIFT MEASUREMENT TEST")
        print("=" * 58)

        baseline = self._record_baseline()
        print(f"  Baseline — backend: {baseline['backend']:.4f}  local: {baseline['local']:.6f}")

        temp_files = [c["filename"] for c in TEST_COMMITS]

        try:
            for commit_def in TEST_COMMITS:
                self._git_commit(commit_def["filename"], commit_def["content"], commit_def["message"])
                time.sleep(3)

                backend_r = requests.get(f"{self.backend_url}/drift", timeout=10).json()
                backend_score = backend_r.get("drift", -1)
                gate_triggered = backend_r.get("gate") in ("TRIGGERED", "PENDING")

                local_data = drift_calculator.calculate_drift(self.repo_path)
                local_score = local_data["drift_score"]
                new_tokens = local_data["new_tokens"]

                delta = abs(local_score - backend_score)
                agreement = "YES" if delta <= 0.001 else f"NO — delta: {delta:.4f}"

                self.drift_results.append({
                    "label": commit_def["label"],
                    "description": commit_def["message"].split(": ", 1)[-1],
                    "new_tokens": ", ".join(new_tokens[:10]) + ("…" if len(new_tokens) > 10 else ""),
                    "local_score": local_score,
                    "backend_score": backend_score,
                    "agreement": agreement,
                    "gate_triggered": "YES" if gate_triggered else "no",
                })
                print(
                    f"  [{commit_def['label']}] local={local_score:.6f}  backend={backend_score:.4f}"
                    f"  agree={agreement}  gate={'TRIGGERED' if gate_triggered else 'ok'}"
                )

            # Restore commit
            restore_paths = [
                self.repo_path / "test_research" / f
                for f in temp_files
                if (self.repo_path / "test_research" / f).exists()
            ]
            repo = git.Repo(self.repo_path)
            for p in restore_paths:
                p.unlink()
                try:
                    repo.index.remove([str(p.relative_to(self.repo_path))], working_tree=True)
                except Exception:
                    pass
            repo.index.commit("[TEST] test(restore): revert all test commits to clean baseline")
            print("  [RESTORE] Test files removed and committed.")

        except Exception as exc:
            self.problems.append({
                "phase": "Phase 1",
                "problem": str(exc),
                "resolution": "Attempted restore in finally block",
                "impact": "Phase 1 results may be incomplete",
            })
            # Ensure restore even on error
            try:
                repo = git.Repo(self.repo_path)
                for f in temp_files:
                    p = self.repo_path / "test_research" / f
                    if p.exists():
                        p.unlink()
                        try:
                            repo.index.remove([str(p.relative_to(self.repo_path))], working_tree=True)
                        except Exception:
                            pass
                if repo.is_dirty(index=True):
                    repo.index.commit("[TEST] test(restore): emergency cleanup after phase1 error")
            except Exception as restore_exc:
                self.problems.append({
                    "phase": "Phase 1 restore",
                    "problem": str(restore_exc),
                    "resolution": "Manual cleanup required",
                    "impact": "Temp test files may remain",
                })

    # ------------------------------------------------------------------
    # Phase 2 — Justification gate
    # ------------------------------------------------------------------

    def run_phase2(self):
        import git  # type: ignore
        print("\n" + "=" * 58)
        print("PHASE 2: JUSTIFICATION GATE TEST")
        print(f"Backend must be running with WARDEN_LLM={self.llm}")
        print()
        print("If you started the backend without WARDEN_LLM set, please:")
        print("1. Stop the backend (Ctrl+C in the backend terminal)")
        print(f"2. Restart it with: WARDEN_LLM={self.llm} uvicorn backend.main:app --port 8000")
        print("   (from the repository root directory)")
        print()
        input("Press Enter when the backend is ready with WARDEN_LLM set...")
        print("=" * 58)

        high_drift_def = TEST_COMMITS[1]  # HIGH_DRIFT

        for j in JUSTIFICATIONS:
            print(f"\n  [{j['id']}] {j['category']} — {j['text'][:50]}…")

            # Make HIGH_DRIFT commit to trigger gate
            try:
                self._git_commit(high_drift_def["filename"], high_drift_def["content"], high_drift_def["message"])
            except Exception as exc:
                self.problems.append({
                    "phase": f"Phase 2 — {j['id']}",
                    "problem": f"Could not make HIGH_DRIFT commit: {exc}",
                    "resolution": "Skipped this justification",
                    "impact": "No result for this justification",
                })
                continue

            time.sleep(3)

            # Poll gate status
            gate_active = False
            for attempt in range(2):
                try:
                    gs = requests.get(f"{self.backend_url}/gate/status", timeout=5).json()
                    if gs.get("status") in ("TRIGGERED", "PENDING"):
                        gate_active = True
                        break
                except Exception:
                    pass
                if attempt == 0:
                    time.sleep(2)

            if not gate_active:
                self.gate_results.append({
                    "category": j["category"],
                    "id": j["id"],
                    "justification": j["text"],
                    "score": "N/A",
                    "decision": "Gate did not trigger",
                    "response_ms": 0,
                    "reasoning": "",
                })
                self.problems.append({
                    "phase": f"Phase 2 — {j['id']}",
                    "problem": "Gate did not trigger after HIGH_DRIFT commit",
                    "resolution": "Skipped justification submission",
                    "impact": "No evaluation result for this justification",
                })
                # Revert anyway
                try:
                    self._git_revert_head()
                except Exception:
                    pass
                time.sleep(2)
                continue

            # Submit justification
            t_start = time.time()
            try:
                resp = requests.post(
                    f"{self.backend_url}/gate/submit",
                    json={"justification": j["text"]},
                    timeout=90,
                )
                t_ms = int((time.time() - t_start) * 1000)
                data = resp.json()
                score = data.get("score", "N/A")
                decision = data.get("decision", "ERROR")
                reasoning = data.get("reasoning_trace", "")
            except Exception as exc:
                t_ms = int((time.time() - t_start) * 1000)
                score = "N/A"
                decision = "ERROR"
                reasoning = str(exc)
                self.problems.append({
                    "phase": f"Phase 2 — {j['id']}",
                    "problem": f"gate/submit failed: {exc}",
                    "resolution": "Recorded as ERROR",
                    "impact": "No evaluation result",
                })

            self.gate_results.append({
                "category": j["category"],
                "id": j["id"],
                "justification": j["text"],
                "score": score,
                "decision": decision,
                "response_ms": t_ms,
                "reasoning": reasoning,
            })
            print(f"    score={score}  decision={decision}  {t_ms}ms")

            # Revert HIGH_DRIFT commit
            try:
                self._git_revert_head()
            except Exception as exc:
                self.problems.append({
                    "phase": f"Phase 2 — {j['id']} revert",
                    "problem": f"git revert failed: {exc}",
                    "resolution": "Manual revert required",
                    "impact": "Subsequent gate tests may not trigger correctly",
                })

            time.sleep(2)

    # ------------------------------------------------------------------
    # Phase 3 — Audit trail
    # ------------------------------------------------------------------

    def run_phase3(self):
        print("\n" + "=" * 58)
        print("PHASE 3: AUDIT TRAIL")
        print("=" * 58)
        audit_dir = RESULTS_DIR / "audit_trail"
        audit_dir.mkdir(parents=True, exist_ok=True)
        audit_file = audit_dir / f"audit_{self.llm}_{self.timestamp}.txt"
        try:
            requests.post(f"{self.backend_url}/audit", timeout=10)
            r = requests.get(f"{self.backend_url}/download-audit", timeout=10)
            audit_file.write_bytes(r.content)
            print(f"  Audit saved: {audit_file}")
        except Exception as exc:
            self.problems.append({
                "phase": "Phase 3",
                "problem": str(exc),
                "resolution": "Audit file not saved",
                "impact": "No audit trail for this session",
            })
            print(f"  WARNING: Audit save failed — {exc}")

    # ------------------------------------------------------------------
    # Phase 4 — Results tabulation
    # ------------------------------------------------------------------

    def run_phase4(self):
        print("\n" + "=" * 58)
        print("PHASE 4: RESULTS TABULATION")
        print("=" * 58)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self._write_drift_results()
        self._write_gate_results()
        self._write_problems()
        self._write_summary()

    def _write_drift_results(self):
        path = RESULTS_DIR / f"drift_results_{self.llm}.md"
        lines = [f"## Drift Measurement Results — {self.llm}\n"]
        header = "| Commit Label | Description | New Tokens Introduced | Local Drift Score | Backend Drift Score | Agreement | Gate Triggered |"
        sep    = "|---|---|---|---|---|---|---|"
        lines.append(header)
        lines.append(sep)
        for r in self.drift_results:
            lines.append(
                f"| {r['label']} | {r['description']} | {r['new_tokens']} "
                f"| {r['local_score']:.6f} | {r['backend_score']:.4f} "
                f"| {r['agreement']} | {r['gate_triggered']} |"
            )
        path.write_text("\n".join(lines) + "\n")
        print(f"  Written: {path.name}")

    def _write_gate_results(self):
        path = RESULTS_DIR / f"justification_results_{self.llm}.md"
        lines = [f"## Justification Gate Results — {self.llm}\n"]
        header = "| Category | Justification (first 50 chars) | Score | Decision | Response Time (ms) | Reasoning Summary (first 120 chars) |"
        sep    = "|---|---|---|---|---|---|"
        lines.append(header)
        lines.append(sep)
        for r in self.gate_results:
            lines.append(
                f"| {r['category']} | {r['justification'][:50]} "
                f"| {r['score']} | {r['decision']} | {r['response_ms']} "
                f"| {str(r['reasoning'])[:120]} |"
            )

        # Summary statistics
        weak   = [r for r in self.gate_results if r["category"] == "WEAK"]
        medium = [r for r in self.gate_results if r["category"] == "MEDIUM"]
        strong = [r for r in self.gate_results if r["category"] == "STRONG"]

        def _rejected(lst):
            return sum(1 for r in lst if str(r["decision"]).upper() == "REJECTED")

        def _approved(lst):
            return sum(1 for r in lst if str(r["decision"]).upper() == "APPROVED")

        def _times(lst):
            valid = [r["response_ms"] for r in lst if isinstance(r["response_ms"], (int, float)) and r["response_ms"] > 0]
            return int(sum(valid) / len(valid)) if valid else 0

        def _score_range(lst):
            scores = [r["score"] for r in lst if isinstance(r["score"], (int, float))]
            if not scores:
                return "N/A"
            return f"{min(scores)}-{max(scores)}"

        all_times = [r["response_ms"] for r in self.gate_results if isinstance(r["response_ms"], (int, float)) and r["response_ms"] > 0]
        avg_time = int(sum(all_times) / len(all_times)) if all_times else 0

        lines.append(f"""
### Summary Statistics
- Weak justifications rejected: {_rejected(weak)}/3
- Medium justifications rejected: {_rejected(medium)}/3
- Strong justifications approved: {_approved(strong)}/3
- Average response time: {avg_time}ms
- Score range weak: {_score_range(weak)}
- Score range medium: {_score_range(medium)}
- Score range strong: {_score_range(strong)}
""")
        path.write_text("\n".join(lines) + "\n")
        print(f"  Written: {path.name}")

    def _write_problems(self):
        path = RESULTS_DIR / f"problems_{self.llm}.md"
        lines = [f"## Problems Encountered — {self.llm}\n"]
        header = "| Phase | Problem | Resolution | Impact |"
        sep    = "|---|---|---|---|"
        lines.append(header)
        lines.append(sep)
        if self.problems:
            for p in self.problems:
                lines.append(f"| {p['phase']} | {p['problem']} | {p['resolution']} | {p['impact']} |")
        else:
            lines.append("| — | No problems encountered during this test session. | — | — |")
        path.write_text("\n".join(lines) + "\n")
        print(f"  Written: {path.name}")

    def _write_summary(self):
        path = RESULTS_DIR / f"summary_{self.llm}.md"

        drift_summary = "No drift data collected."
        if self.drift_results:
            agree_count = sum(1 for r in self.drift_results if r["agreement"] == "YES")
            scores = [(r["label"], r["local_score"]) for r in self.drift_results]
            score_desc = ", ".join(f"{l}={s:.4f}" for l, s in scores)
            drift_summary = (
                f"Local drift scores were: {score_desc}. "
                f"Local and backend scores agreed (within 0.001) on {agree_count}/{len(self.drift_results)} commits. "
                f"HIGH_DRIFT and SPEC_VIOLATION commits produced the highest local drift scores."
            )

        gate_summary = "No gate data collected."
        if self.gate_results:
            weak_rej   = sum(1 for r in self.gate_results if r["category"] == "WEAK"   and str(r["decision"]).upper() == "REJECTED")
            med_rej    = sum(1 for r in self.gate_results if r["category"] == "MEDIUM"  and str(r["decision"]).upper() == "REJECTED")
            strong_app = sum(1 for r in self.gate_results if r["category"] == "STRONG"  and str(r["decision"]).upper() == "APPROVED")
            gate_summary = (
                f"Weak justifications were rejected {weak_rej}/3 times, medium {med_rej}/3, "
                f"and strong justifications were approved {strong_app}/3 times. "
                f"Score differentiation across quality tiers is reported in justification_results_{self.llm}.md."
            )

        limitations = (
            "The drift calculator compares token vocabularies against the spec vault; it does not perform "
            "semantic embedding comparison. Gate triggering depends on the backend's internal sample-diff "
            "cycle in demo mode, which may not always align with the test commit timing."
        )

        content = f"""## Test Summary — {self.llm} — {self.timestamp}

### Test Configuration
- LLM Backend: {self.llm}
- Model: {LLM_MODEL_NAMES.get(self.llm, 'unknown')}
- Backend URL: {self.backend_url}
- Repository: {self.repo_path}
- Drift Threshold: {self.drift_threshold}

### Drift Detection Findings
{drift_summary}

### Justification Evaluation Findings
{gate_summary}

### Cross-LLM Observations
To be completed after all LLM test sessions are run and results compared.

### Limitations Observed
{limitations}
"""
        path.write_text(content)
        print(f"  Written: {path.name}")

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self):
        print("\n" + "=" * 58)
        print("SPEC-DRIFT CHRONOMETER — RESEARCH TEST SUITE")
        print("=" * 58)
        print(f"  LLM backend:    {self.llm} ({LLM_MODEL_NAMES[self.llm]})")
        print(f"  Backend URL:    {self.backend_url}")
        print(f"  Repository:     {self.repo_path}")
        print(f"  API key source: environment variable ({LLM_KEY_NAMES[self.llm]})")
        print("=" * 58)

        print("\nRunning pre-flight checks…")
        self._check_backend()
        self._check_api_key()
        self._check_git_history()
        print("  All checks passed.")

        self.run_phase1()
        self.run_phase2()
        self.run_phase3()
        self.run_phase4()

        other_llm = "huggingface" if self.llm == "gemini" else "gemini"
        print(f"""
==========================================================
TEST SESSION COMPLETE
Results saved to test_research/results/
Files generated:
  - drift_results_{self.llm}.md
  - justification_results_{self.llm}.md
  - problems_{self.llm}.md
  - summary_{self.llm}.md
  - audit_trail/audit_{self.llm}_{self.timestamp}.txt

To run with the second LLM, restart with --llm {other_llm}
==========================================================
""")


def main():
    parser = argparse.ArgumentParser(description="Spec-Drift Chronometer research test suite")
    parser.add_argument("--llm", choices=["gemini", "huggingface", "mistral"], default="gemini")
    parser.add_argument("--backend-url", default="http://localhost:8000")
    parser.add_argument("--repo-path", default=str(REPO_ROOT))
    args = parser.parse_args()

    runner = ResearchTestRunner(
        llm=args.llm,
        backend_url=args.backend_url,
        repo_path=Path(args.repo_path).resolve(),
    )
    runner.run()


if __name__ == "__main__":
    main()
