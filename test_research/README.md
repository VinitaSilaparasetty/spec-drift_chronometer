# Spec-Drift Chronometer — Research Test Suite

Empirical test suite for the IEEE Software paper:
*"Failure Modes in EU AI Act Article 14 Compliance Engineering: Empirical Evidence
from a Production Warden Agent"*

---

## Reproducing the Results

### What you need

- Python 3.12+
- Git
- A **Mistral API key** (free trial credits available at console.mistral.ai — this is the only external dependency)

That is all. No AWS account. No HuggingFace Pro. No local GPU.

### Setup (one-time)

```bash
git clone https://github.com/VinitaSilaparasetty/spec-drift_chronometer.git
cd spec-drift_chronometer
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt -r test_research/requirements.txt
```

### Run the failure mode tests (FM1, FM3–FM6, FM10–FM12)

Open two terminals.

**Terminal 1 — start the backend:**
```bash
source venv/bin/activate
DEMO_MODE=false WARDEN_LLM=mistral MISTRAL_API_KEY=your-key \
  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — run the tests:**
```bash
source venv/bin/activate
cd test_research
MISTRAL_API_KEY=your-key python run_failure_modes.py
```

The script takes approximately 8–10 minutes. It manages the backend internally
(restarts it between tests that need a fresh gate state, and spawns a second
instance on port 8001 for the FM11 invalid-credentials test). All git commits
made during drift tests are reverted automatically.

Results are written to `results/failure_modes_raw.txt` (full output) and
`results/failure_modes_summary.md` (IEEE paper table).

### Run the justification quality tests (9-level WEAK/MEDIUM/STRONG suite)

With the backend running (same Terminal 1 command as above):

```bash
cd test_research
MISTRAL_API_KEY=your-key python run_tests.py --llm mistral
```

Results are written to `results/raw_results_mistral.txt` and
`results/justification_results_mistral.md`.

---

## Expected Results

### Failure mode tests

| FM | Expected verdict | Key number |
|----|-----------------|------------|
| FM1 | CONFIRMED | No identity check on /gate/submit — any caller accepted |
| FM3 | CONFIRMED | Drift drops from ~0.011 to ~0.004 after spec vault injection |
| FM4 | CONFIRMED | Drift score identical before and after gate submissions |
| FM5 | CONFIRMED | Sub-threshold commit produces zero audit trail entry |
| FM6 | CONFIRMED | No commit SHAs appear in audit trail |
| FM10 | MITIGATED | Mistral catches MD5/bcrypt error — score ~10/100, REJECTED |
| FM11 | CONFIRMED | Invalid key → HTTP 200 REJECTED with error buried in reasoning trace |
| FM12 | PARTIAL | No X-AI-Used header; model field present in JSON body only |

FM10 depends on the LLM's training data covering the specific vulnerability being
tested. MD5/bcrypt is well-known; the mitigation may not hold for obscure
cryptographic errors.

### Justification quality tests

| Quality | Expected score | Expected decision |
|---------|---------------|-------------------|
| WEAK (1–2 words) | 0–5/100 | REJECTED |
| MEDIUM (vague sentence) | 10/100 | REJECTED |
| STRONG (specific, traceable) | 91–95/100 | APPROVED |

LLM responses include stochastic variation. Score ranges are approximate (±5–10
points across runs). Decision outcomes (APPROVED / REJECTED) are stable.

---

## Notes for Reproducibility

**LLM non-determinism:** Mistral's scores will vary slightly between runs. The
decisions (APPROVED / REJECTED) are stable; individual scores may shift by ±5–10
points. This matches the published results.

**Gate state resets:** The failure mode script restarts the backend between tests
that require a fresh gate state. If you interrupt the script mid-run, kill any
remaining backend processes (`pkill -f "uvicorn backend.main"`) and re-run from
the start.

**FM3 spec vault cleanup:** FM3 temporarily modifies `.kiro/steering/governance.md`
and makes git commits. Both are reverted automatically via `git reset --hard`.
If the script is interrupted during FM3, run `git status` — if governance.md
shows as modified, run `git checkout .kiro/steering/governance.md`.

**Results directory:** Running the tests overwrites `results/failure_modes_raw.txt`
and related files. The committed results in the repository represent the exact run
used for the paper.

**Windows:** The `restart_main_backend()` function uses `pkill`, which is not
available on Windows. Run the failure mode tests on macOS or Linux, or use WSL.

---

## What each script does

### `run_failure_modes.py`

Tests eight specific failure modes against the live backend. Each test function is
self-contained: it makes API calls, optionally makes and reverts git commits, and
returns a structured finding. The script manages two backend instances (main on
port 8000, isolated on port 8001 for FM11).

### `run_tests.py`

Three-phase test runner:
1. **Drift measurement** — makes five test commits with different vocabulary profiles
   and records the drift score for each
2. **Justification gate** — submits nine justifications at three quality levels and
   records the LLM's score and decision for each
3. **Audit trail** — calls POST /audit and verifies the output file

### `drift_calculator.py`

Standalone drift scorer. Can be imported directly without a running backend:

```python
from drift_calculator import calculate_drift
result = calculate_drift()  # reads HEAD~1..HEAD from current repo
print(result["drift_score"], result["new_tokens"])
```

---

## API Key Notes

| Provider | Key variable | Free tier | Notes |
|----------|-------------|-----------|-------|
| Mistral | `MISTRAL_API_KEY` | Yes (trial credits) | Recommended. Reliable from all environments. |
| Gemini | `GEMINI_API_KEY` | Yes | Works but not tested across all failure modes |
| HuggingFace | `HF_API_KEY` | **Pro required** | Free keys return auth errors on the inference router |
