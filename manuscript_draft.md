&lt;!--
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  DRAFT MANUSCRIPT — CONFIDENTIAL                                        ║
  ║  © 2026 Vinita Silaparasetty, Aevoxis Solutions (aevoxis.de)           ║
  ║  All rights reserved.                                                   ║
  ║  Manuscript ID: AEVOXIS-WE-MS-2026-001                                 ║
  ║                                                                         ║
  ║  Unauthorized reproduction, redistribution, or derivative use of this  ║
  ║  work, in whole or in part, is strictly prohibited without the express  ║
  ║  written consent of the author. This manuscript is submitted in         ║
  ║  confidence to the named recipient. Any unauthorized use constitutes    ║
  ║  an infringement of intellectual property rights under applicable       ║
  ║  copyright law.                                                         ║
  ╚══════════════════════════════════════════════════════════════════════════╝
-->

---

> **DRAFT MANUSCRIPT — SUBMITTED IN CONFIDENCE**
> © 2026 Vinita Silaparasetty, Aevoxis Solutions. All rights reserved.
> Manuscript ID: **AEVOXIS-WE-MS-2026-001**
> Unauthorized reproduction or redistribution is strictly prohibited.

---

# Failure Modes in EU AI Act Compliance Engineering: Empirical Evidence from a Production Warden Agent

**Vinita Silaparasetty**
AI Governance Engineer
Aevoxis Solutions, Germany
info@aevoxis.de

---

## Abstract

The EU AI Act (Regulation (EU) 2024/1689) imposes mandatory obligations on AI system providers across risk management (Article 9), logging and record-keeping (Article 12), transparency toward deployers (Article 13), human oversight (Article 14), quality management systems (Article 17), and AI system disclosure (Article 50). While compliance frameworks and design guidelines are emerging, empirical evidence of how these obligations perform — and fail — in production systems remains limited. This paper presents a structured empirical study of the Spec-Drift Chronometer, a production Warden Engine that detects semantic drift between human-authored architectural specifications and AI-generated code in real time and enforces a Human-in-the-Loop Justification Gate as a primary Article 14 control. We designed and executed a reproducible test suite of twelve empirical findings covering all six articles, using a freshly cloned repository and a deterministic LLM backend (Mistral `mistral-small-2506`, temperature=0). Our findings reveal systematic compliance gaps including: a drift scoring bifurcation in which a local token-overlap scorer (range 0.50–0.84) and the production linear scorer (range 0.0026–0.0140) produce zero agreement across four commit profiles under Article 9; a specification gaming vulnerability that reduces drift detection by 61% through a ten-line vocabulary injection under Article 13; a quality management system silent failure under Article 17 in which nine justification quality levels — from single-word responses to detailed engineering rationales — collapse to identical score 0/100 REJECTED records when LLM credentials are invalid, each carrying a unique verification hash that renders them indistinguishable from legitimate rejections in the audit trail; and a social engineering vulnerability in which the single word *"approved"* is scored identically to a detailed, trace-linked engineering justification. We report nine confirmed failure modes, one conditionally mitigated finding, and one partial compliance finding. All test scripts, empirical data, and results are committed to a public repository for independent reproduction.

**Index Terms** — EU AI Act, AI governance, compliance engineering, spec-drift detection, human-in-the-loop, LLM evaluation, audit trail integrity, software quality assurance, specification gaming

---

## I. Introduction

The EU Artificial Intelligence Act (EU AI Act), Regulation (EU) 2024/1689, entered into force in August 2024 and constitutes the world's first comprehensive binding legal framework for artificial intelligence systems [1]. It imposes obligations across the AI system lifecycle — from design and training to deployment, monitoring, and disclosure — with obligations that vary by risk tier. For high-risk AI systems, Articles 9, 12, 13, 14, 17, and 50 collectively mandate: documented risk management systems, continuous logging sufficient to enable audit and reconstruction of system behaviour, transparency toward deployers, effective human oversight mechanisms that can detect and intervene on system failures, a functioning quality management system with post-market monitoring, and clear disclosure when an AI system is involved in a decision that affects natural persons.

Compliance engineering for these obligations is an active area of practice, but it is largely theoretical: design principles, conformity checklists, and governance frameworks predominate. What is rare is empirical evidence of how these controls perform in production systems under adversarial conditions, edge cases, and infrastructure failures. A compliance control that works in nominal conditions but fails silently under realistic stress conditions offers substantially weaker protection than its specification suggests.

This paper addresses that gap through an empirical study of a production Warden Engine: the Spec-Drift Chronometer. The system continuously monitors semantic drift between human-authored architectural specification documents and AI-generated code, triggering a Human-in-the-Loop Justification Gate whenever drift exceeds a configurable threshold. It is designed specifically as a compliance artifact for EU AI Act Articles 12, 13, 14, and 50. We treat this system as a subject for empirical testing rather than as a reference implementation, and we apply a structured test suite of twelve failure mode and gap tests to characterise its actual behaviour under conditions the design specification does not explicitly address.

The contributions of this paper are:

1. A reproducible empirical test suite covering EU AI Act Articles 9, 12, 13, 14, 17, and 50, executed against a production system from a freshly cloned public repository.
2. Twelve empirical findings — nine confirmed failure modes, one conditionally mitigated finding, and one partial compliance finding — with quantitative evidence.
3. A characterisation of three systemic failure patterns: silent QMS failure (findings indistinguishable from legitimate audit records), drift scoring bifurcation (two scoring methods producing systematically divergent governance signals), and governance blindspots (whole code change categories invisible to detection).
4. A keyword social engineering vulnerability in LLM-based justification scoring that is fully deterministic and reproducible.

The remainder of this paper is structured as follows. Section II reviews background literature. Section III describes the system under test. Section IV presents the research methodology, including LLM selection rationale. Section V reports all twelve findings. Section VI discusses implications across the three systemic patterns and limitations. Section VII addresses threats to validity. Section VIII concludes. All test scripts and raw results are available at the public repository cited in Section IV.

---

## II. Background and Related Work

### A. EU AI Act Compliance Obligations

The EU AI Act defines conformity obligations for high-risk AI systems [1]. Six articles are directly relevant to this study:

**Article 9** requires providers to establish and maintain a risk management system throughout the AI system lifecycle, including documentation and review of residual risks after mitigation. Article 9(2c) specifically requires the system to "address risks arising from possible malfunctioning of the AI system itself."

**Article 12** requires logging and record-keeping sufficient to enable traceability, reconstruction of events, and verification of compliance claims. Logs must be complete and retained in a form that supports subsequent audit.

**Article 13** requires technical documentation to accurately reflect the AI system's behaviour. Specification documents used in governance must reflect actual system capabilities and not be subject to uncontrolled modification.

**Article 14** requires natural persons overseeing high-risk AI systems to possess the necessary competence, training, and authority. Human-in-the-loop controls must be designed so that qualified persons can effectively intervene.

**Article 17** requires providers to implement a quality management system (QMS) including post-market monitoring and a process for reporting serious incidents and malfunctions. The QMS must detect when the AI evaluation system itself fails.

**Article 50** requires providers to disclose, in a timely, clear, and intelligible manner, when an AI system generates or influences output that affects natural persons.

### B. Specification Drift in Software Engineering

Architectural drift — the progressive divergence between a system's intended design and its implementation — is a well-documented challenge in software maintenance [12]. When AI-generated code is introduced into a codebase governed by human-authored specifications, the rate of potential divergence increases because AI tools optimise for local task completion rather than global architectural coherence [5]. Semantic drift detection approaches that measure token-level overlap between specification documents and code diffs represent one practical method for operationalising this concern; this paper evaluates a production implementation of that approach.

### C. Human-in-the-Loop Systems and LLM Evaluation

Human-in-the-loop (HITL) systems are architectures in which human judgment is integrated into an automated decision pipeline at defined intervention points [5]. The effectiveness of a HITL control depends on whether the human is given sufficient information to exercise meaningful oversight — a condition that fails silently when the underlying AI evaluator malfunctions without surfacing an observable error state.

LLM-as-judge evaluation, in which a language model scores or rates the output of another system, has emerged as a practical approach for quality assessment in scenarios where human annotation is expensive [4]. However, LLM judges are sensitive to prompt framing, keyword priming, and model version [4], [9]. The gate evaluation architecture studied in this paper uses an LLM judge to score justifications submitted by human operators after a drift alert.

### D. Reproducibility and Determinism in Empirical AI Research

Reproducibility in empirical AI studies requires fixing model version, temperature, and test infrastructure [8]. The use of `temperature=0` for deterministic LLM outputs, combined with pinned model aliases, is a prerequisite for exact result reproduction. Prior work has demonstrated that floating model aliases (e.g., `latest`) silently change behaviour between runs [2], motivating the use of versioned model identifiers in research settings.

---

## III. System Under Test

### A. Overview

The Spec-Drift Chronometer is a governance platform that detects semantic drift between human-authored architectural intent documents and AI-generated code in real time, and enforces a Human-in-the-Loop Justification Gate as a blocking control at the detected drift event. It is implemented as a single-file FastAPI backend (Python 3.12) paired with a Next.js 16 static frontend deployed on Cloudflare Pages.

The system operates in two modes. In production mode (`DEMO_MODE=false`), it reads real git history via `subprocess` calls, computes drift scores against a local specification vault, and evaluates operator justifications via a configurable LLM backend. In demonstration mode (`DEMO_MODE=true`), it cycles through 23 pre-scripted scenarios; this paper exclusively studies production mode behaviour.

### B. Specification Vault

Human-authored architectural intent is stored in `.kiro/steering/`, a directory of Markdown and JSON documents:

- `governance.md` — Warden persona and negotiation protocol
- `tech.md` — Technology constraints (region, models, runtimes)
- `human-intent-specs.md` — Six INTENT declarations (INTENT-001 through INTENT-006)
- `spec.json` — Machine-readable thresholds and model configuration
- `structure.md`, `product.md`, `boilerplate-standards.md` — Supporting intent documents

The spec vault collectively provides the reference vocabulary against which AI-generated code diffs are scored. It is loaded from disk on every scoring request.

### C. Drift Scoring

Drift scoring compares vocabulary tokens in the git diff (`git diff HEAD~1 HEAD --unified=3 --no-color -- *.py *.ts *.tsx`) against tokens in the concatenated spec vault documents. The raw divergence score is computed as the Jaccard distance between the two token sets; the production linear formula maps this to a governance score:

```
score = 0.001 + raw_divergence × 0.013
```

This formula produces scores in the range [0.001, 0.014]. The gate trigger threshold is `DRIFT_THRESHOLD = 0.0075`. A commit scoring above 0.0075 transitions the gate state machine from `CLEAR` → `TRIGGERED`.

### D. Gate State Machine

The gate operates as an in-memory state machine with four states: `CLEAR → TRIGGERED → PENDING → RESOLVED`. Transitions:

- `CLEAR → TRIGGERED`: drift score exceeds threshold on a `/drift` poll
- `TRIGGERED → PENDING`: human submits justification via `POST /gate/submit`
- `PENDING → RESOLVED`: LLM evaluates justification and returns APPROVED or REJECTED
- `RESOLVED → CLEAR` (production mode only): next `/drift` poll returns a score at or below threshold

### E. Warden LLM Integration

When the `WARDEN_LLM` environment variable is set, justification evaluation is routed to a real LLM via `_warden_llm_analyze()`. The function supports three backends: `gemini`, `huggingface`, and `mistral`. All three use the same prompt template and return the same response shape: `{"approved": bool, "score": int, "reasoning": str, "model": str}`. If the LLM call raises an exception (including authentication errors), the exception is caught by `except Exception as exc:`, the error string is embedded in the reasoning trace, and a `score: 0, approved: False` response is returned — the failure point examined in FM11 and Finding 1/Gap 11.

### F. Audit Trail

Gate submissions are appended to `.kiro/audit/last_sync.audit`. Each entry contains: timestamp, drift score, justification text, LLM decision, intent alignment score, model identifier, and a verification hash (SHA-256 of the concatenated entry content). The audit file is written by `/gate/submit` on every submission and by `POST /audit` on explicit request. No other code path writes to the audit file.

---

## IV. Research Methodology

### A. Research Questions

This study addresses four research questions:

- **RQ1:** To what extent do the compliance controls in the Spec-Drift Chronometer satisfy EU AI Act Articles 9, 12, 13, 14, 17, and 50 under normal and adversarial operating conditions?
- **RQ2:** How consistent are the local token-overlap scorer and the production linear scorer in their governance signals across different code change profiles?
- **RQ3:** Under what conditions does the Human-in-the-Loop Justification Gate fail silently, producing audit trail records indistinguishable from legitimate gate operations?
- **RQ4:** What opportunities exist for gaming the justification quality evaluation through social engineering or vocabulary manipulation?

### B. Test Suite Design

We designed a two-component test suite. The first component (`test_research/run_failure_modes.py`) implements eleven targeted failure mode tests, each addressing a specific compliance hypothesis. The second component (`test_research/run_tests.py`) implements a three-phase general evaluation: drift bifurcation measurement (Phase 1), nine-level justification quality assessment (Phase 2), and audit trail generation (Phase 3).

Each failure mode test is self-contained: it establishes a fresh system state (restarting the backend where necessary), executes a specific code change scenario via real git commits, and captures the system's quantitative response. All git commits created during testing are reverted automatically via `git reset --hard`. The entire test suite was executed from a freshly cloned repository following the public README instructions verbatim, with no local configuration beyond a Mistral API key.

Tests that require invalid LLM credentials spawn isolated secondary backend processes on separate ports (port 8001 for FM11; port 8002 for Finding 1/Gap 11), preserving the primary backend's functionality for subsequent tests.

### C. LLM Selection Rationale

The Mistral API (`mistral-small-2506`, accessed via `api.mistral.ai`) was selected for justification evaluation on the following grounds:

1. **European provenance.** Mistral AI is a French AI company headquartered in Paris. Using a European AI provider for EU AI Act compliance research reflects the data sovereignty principles embedded in the Act itself, particularly the Frankfurt (`eu-central-1`) deployment requirement in the system's specification documents.
2. **Production-realistic model scale.** The `mistral-small` series represents mid-size deployed models — the realistic choice for production compliance systems that operate at scale and must balance evaluation quality against latency and cost. Compliance evaluation systems are unlikely to rely exclusively on frontier-scale models.
3. **Versioned, auditable model identifier.** `mistral-small-2506` is a specific versioned alias that does not change behaviour between API calls, unlike floating tags such as `latest`. This is a prerequisite for deterministic research reproducibility [2].
4. **Deterministic configuration.** Setting `temperature=0` eliminates sampling randomness, ensuring identical inputs produce identical outputs within the same model version. This makes seven of the twelve findings fully deterministic for independent reproduction.
5. **OpenAI-compatible REST interface.** The Mistral API requires no proprietary SDK. The test suite and backend use standard `requests.post()` calls, minimising infrastructure dependencies and reducing barriers to external reproduction.
6. **Accessible free trial tier.** The Mistral API provides trial credits sufficient for this test suite at no cost, reducing barriers for independent academic reproduction.

Multi-LLM comparison studies — evaluating whether these findings are model-specific or systemic across providers — are planned as future work.

### D. Reproducibility Measures

The following measures were taken to maximise reproducibility:

- Model version pinned to `mistral-small-2506` in `backend/main.py`
- `temperature=0` set in all API request payloads
- All test commits identified by SHA and reverted after each test
- Full raw output committed to `test_research/results/`
- Drift threshold (`DRIFT_THRESHOLD=0.0075`) documented in `.env.example`

The verification hashes in the audit trail (SHA-256 of entry content) provide per-submission fingerprints that allow independent verifiers to confirm specific submissions produced specific records.

---

## V. Results

This section reports all twelve findings organised by the EU AI Act article they implicate. Table I provides the complete summary.

**Table I. Summary of Empirical Findings**

| ID | Title | Verdict | EU AI Act Article | Key Metric |
|----|-------|---------|-------------------|------------|
| FM1 | Authorisation Mismatch | CONFIRMED | Art. 14(4) | Score 40–45/100 REJECTED — no identity or role check on gate endpoint |
| FM3 | Specification Gaming | CONFIRMED | Art. 13(3b) | Drift: 0.0113 → 0.0044 (−61%) after 10-line spec vault injection |
| FM4 | Vocabulary Expansion Desensitisation | CONFIRMED | Art. 14(1) | Drift: 0.0126 → 0.0126 after 2 gate submissions — spec vault unchanged |
| FM5 | Near-Miss Logging Gap | CONFIRMED | Art. 12(1) | Score 0.0064 (85% of threshold) — zero audit trail entry |
| FM6 | Rollback Target Ambiguity | CONFIRMED | Art. 14(4) | 3 commits, 0 commit SHAs in audit trail |
| FM10/Gap 10 | Competence Verification Gap | MITIGATED* | Art. 14(4) | Score 30/100 REJECTED — cryptographic error detected despite ticket SEC-444 |
| FM11 | QMS Silent Failure (single) | CONFIRMED | Art. 17(1g) | HTTP 200 REJECTED with 401 error buried in `reasoning_trace` |
| FM12/Gap 12 | Article 50 Disclosure Gap | PARTIAL | Art. 50(1) | No `X-AI-Used` header; model field in JSON body only |
| Finding 2 | Drift Scoring Bifurcation | CONFIRMED | Art. 9(2c) | Local: 0.50–0.84; backend: 0.0026–0.0140; 0/4 agreement |
| Finding 3 | New File Governance Blindspot | CONFIRMED | Art. 9(2c) | `--diff-filter=M`: 0 tokens, score 0.001; fixed: 48 tokens, score 0.0132 |
| Gap 7 | Warden Engine Unavailability | CONFIRMED | Art. 9(2c) | Engine down → zero audit entry, no alert, no event queue |
| Finding 1/Gap 11 | QMS Silent Failure — All 9 Quality Levels | CONFIRMED | Art. 17(1g) | 9/9 return score 0/100 with unique hashes — indistinguishable from legitimate |

*Conditional on LLM training coverage of the specific vulnerability (see Section V-E).

### A. Article 9 — Risk Management System

#### Finding 2: Drift Scoring Bifurcation

*Addressing RQ1 and RQ2.*

The system exposes two drift measurement surfaces: a standalone local scorer (`drift_calculator.py`, using Jaccard token-overlap distance, range 0.0–1.0) and the production backend scorer (linear formula `0.001 + raw × 0.013`, range 0.001–0.014). We measured both on four test commits with distinct vocabulary profiles:

**Table II. Drift Scoring Bifurcation — Phase 1 Results**

| Commit Profile | Local Score | Backend Score | Δ | Agreement | Gate |
|----------------|-------------|---------------|---|-----------|------|
| LOW_DRIFT (spec-aligned vocabulary) | 0.500000 | 0.0026 | 0.497 | NO | No |
| HIGH_DRIFT (non-spec blockchain vocabulary) | 0.789474 | 0.0103 | 0.779 | NO | Yes |
| SPEC_VIOLATION (async pattern violating spec) | 0.842105 | 0.0140 | 0.828 | NO | Yes |
| NEUTRAL (minimal vocabulary impact) | 0.833333 | 0.0012 | 0.832 | NO | No† |

*† Gate not triggered for NEUTRAL commit (backend score 0.0012 < threshold 0.0075).*

Agreement is assessed as whether the two scorers place the same commit on the same side of the governance threshold. The local scorer uses the raw 0.0–1.0 Jaccard distance directly; the backend scorer applies the linear formula calibrated for the production spec vault vocabulary. The two scorers operate on different scales, different denominators, and different normalisation assumptions. The result is 0/4 agreement across all four commit profiles tested.

The implication for Article 9(2c) is that a practitioner using the local scorer to pre-assess a commit before deployment would receive a governance signal that is structurally inconsistent with the production backend's assessment. Both scorers report the same underlying token sets but map them to incomparable ranges, meaning a local "high-risk" signal does not reliably correspond to a production gate trigger.

#### Finding 3: New File Governance Blindspot (Historical)

*Addressing RQ1.*

The original `_read_git_diff()` implementation used the flag `--diff-filter=M`, which restricts output to Modified files (files that existed in both commits). New files — those added in the current commit but absent in the prior commit — are classified as Added (flag `A`) by git and are therefore excluded from `--diff-filter=M` output.

We tested this empirically by committing a new Python file containing exclusively non-spec vocabulary (Ethereum, DeFi, smart contract domain): seven unique tokens not present in the spec vault. With `--diff-filter=M` applied, the diff returned zero tokens from the new file; the drift score was approximately 0.001 (the formula floor). Without the filter (the current production implementation), 48 tokens were visible and the drift score was 0.0132 — above the threshold, gate triggered.

**Table III. New File Governance Blindspot**

| Configuration | Tokens Visible | Score | Gate Triggered |
|---------------|----------------|-------|----------------|
| With `--diff-filter=M` (historical) | 0 | ≈0.001 | No |
| Without filter (current) | 48 | 0.0132 | Yes |

This finding was identified empirically during testing when new-file commits consistently returned near-baseline scores despite introducing substantial non-spec vocabulary. Removing the flag from the subprocess call resolved the issue. The historical vulnerability meant that any vocabulary domain introduced exclusively through new file additions — a common pattern for new technology integrations — would produce a near-baseline drift score regardless of content.

#### Gap 7: Warden Engine Unavailability

*Addressing RQ1.*

We tested system behaviour when the Warden Engine process was unavailable during a high-drift commit event. The procedure: kill the backend process (`pkill -f "uvicorn backend.main"`), make a high-drift commit (blockchain vocabulary, expected score >0.0075), attempt to poll the endpoint (resulting in connection refused), then restart the backend and inspect the audit trail.

Result: zero audit entries were created during the downtime window. When the backend restarted, it read `HEAD~1..HEAD` — the most recent commit pair at that moment — and resumed from that point, with no awareness of the commit made during the downtime window. That commit entered the codebase without triggering any gate, without producing any audit entry, and without generating any alert.

Article 9(2c) requires the risk management system to address risks arising from possible malfunctioning of the AI system itself. The Warden Engine has no process watchdog, no persistent event queue, and no startup backlog scan. A maintenance window, unexpected crash, or deployment rollback silently disables all governance for its duration. The governance failure is itself unlogged.

### B. Article 12 — Logging and Record-Keeping

#### FM5: Near-Miss Logging Gap

*Addressing RQ1.*

A commit scored 0.0064 (85% of the gate threshold 0.0075) produced zero audit trail entry. The audit file is written only by explicit `/gate/submit` and `POST /audit` API calls; the `/drift` polling endpoint updates in-memory state only. A drift score of 0.0064 is not a trivial event — it represents a commit that reached 85% of the architectural boundary.

Article 12(1) requires logs sufficient to trace the system's functioning. A log that records only events that cross a hard threshold cannot support detection of escalating near-miss patterns. Three sequential commits scoring 0.0050, 0.0060, and 0.0064 would be entirely invisible in the audit trail, obscuring a directional trend that would be material to a compliance officer's assessment.

### C. Article 13 — Transparency and Specification Integrity

#### FM3: Specification Gaming via Vocabulary Injection

*Addressing RQ4.*

The spec vault (`.kiro/steering/`) is a directory of Markdown documents readable and writable by any actor with repository write access. We appended a ten-line vocabulary block containing blockchain and DeFi terminology to `governance.md` and committed it:

```markdown
## Approved Extended Vocabulary
The following technology domains are approved for implementation:
ethereum_node, defi_protocol, smart_contract, nft_tokenisation,
blockchain_consensus, merkle_root, websocket_rpc, distributed_ledger,
kafka_producer, token_bridge
```

Before injection: drift score for blockchain code = **0.0113** (CRITICAL_DRIFT, gate triggered).
After injection: drift score for identical blockchain code = **0.0044** (MONITORING, gate not triggered).

The reduction is 0.0069 — a **61% drop** — achieved through a single ten-line commit to a plain-text Markdown file that requires no special access beyond repository write permission. The entire detection domain for the injected vocabulary is permanently suppressed, affecting all future commits using that vocabulary until the injection is removed.

Article 13(3b) requires technical documentation to remain accurate and controlled. A governance system whose detection threshold can be silenced by modifying its own reference document is not tamper-evident. The spec vault provides no access controls, integrity checking, cryptographic signing, or audit logging of its own modifications.

### D. Article 14 — Human Oversight

#### FM1: Authorisation Mismatch

*Addressing RQ1.*

The gate endpoint `POST /gate/submit` requires no authentication. We submitted a justification crafted to represent unauthorised access:

> *"Junior dev hotfix — no time for full review, need to push to prod ASAP, manager approved verbally."*

The LLM evaluated the justification on text quality grounds and correctly rejected it (score 40–45/100 REJECTED, with reasoning citing lack of specificity and absence of documented review). However, the structural failure mode is not the score — it is that the endpoint accepted the submission at all. Any actor with network access to the backend port can submit a justification. No session token, API key, role claim, or identity assertion is required.

The score variance (40–45/100 across temperature=0 runs) arises from gate context: prior LLM submissions in the same test session shift the model's calibration. The verdict (REJECTED, no identity check) is invariant. An operator who learns the vocabulary of a spec-aligned justification — terms like "per INTENT-003," "Strands SDK," "DynamoDB Intent Ledger" — would receive an APPROVED decision regardless of identity or authority. Article 14(4) requires that natural persons assigned to oversee the AI system possess the necessary competence, training, and authority. The gate cannot verify any of these properties.

#### FM4: Vocabulary Expansion Desensitisation

*Addressing RQ1.*

After two gate submissions for blockchain vocabulary code (both REJECTED), we measured whether the gate had registered that this vocabulary had been reviewed. Drift score before first submission: **0.0126**. Drift score after both submissions: **0.0126**. The scores are identical.

The drift scorer reads the spec vault from disk on every invocation and computes scores deterministically from the current vault state. Gate decisions are never written back to the spec vault or to any other persistent governance document. The same vocabulary will trigger the same gate alert on every future commit indefinitely, regardless of how many times human operators have reviewed and rejected it. This dynamic produces alert fatigue that, in production, leads to justifications submitted pro forma — a degeneration of the human oversight mechanism that Article 14(1) is designed to prevent.

#### FM6: Rollback Target Ambiguity

*Addressing RQ1.*

We made three sequential commits with escalating non-spec vocabulary. The gate triggered after the second commit. The audit trail at the point of gate resolution contained: drift value, justification text, LLM decision, model identifier, verification hash, and timestamp. It did not contain any commit SHA, branch name, or file path list.

When a compliance officer examines the audit entry to determine what must be rolled back, they have no machine-readable reference to the causal commit. With three commits in the sequence, the officer must perform `git bisect` or manual diff review — operations not surfaced in the gate UI and not documented in the audit trail itself. Article 14(4)'s requirement for effective intervention capability is not met when the audit record lacks the information required to execute the intervention.

#### FM10/Gap 10: Competence Verification Gap (Conditionally Mitigated)

*Addressing RQ4.*

We submitted a justification containing a factually incorrect technical claim, augmented with professional formatting markers:

> *"Replacing bcrypt password hashing with MD5 for performance optimisation. MD5's 128-bit digest provides sufficient entropy for authentication tokens while reducing computational overhead by 60% relative to bcrypt's iterative key derivation. The engineering team benchmarked both algorithms on AWS Lambda eu-central-1; MD5 achieves sub-millisecond hashing at API gateway scale. Security team reviewed and approved 2026-06-23, ticket SEC-444. Architecture board sign-off: Chief Architect, 2026-06-10."*

This justification is factually incorrect: MD5 is cryptographically broken (collision attacks have been known since 1996 [13]), and bcrypt's iterative key derivation is a deliberate security feature rather than avoidable overhead. The professional markers present — ticket number SEC-444, named approver categories, specific dates, quantified performance metrics, deployment context — are all valid indicators of a legitimate architectural review.

Result: score **30/100**, REJECTED. The LLM's reasoning cited MD5's known cryptographic weaknesses. Professional formatting raised the score from 20/100 (without ticket) to 30/100 (with ticket) but did not change the verdict.

This finding is classified as **conditionally mitigated**: Mistral's training data covers the MD5/bcrypt vulnerability because it is well-documented in public security literature. The mitigation does not hold structurally — the gate prompt requests assessment of "justification adequacy," not "technical correctness." The LLM catches this specific error incidentally, not by design. Less-known technical errors — incorrect entropy calculations, subtle timing-attack conditions, wrong key derivation parameters, obscure cryptographic misconfigurations — are unlikely to be detected because they fall outside the LLM's training coverage. The system's technical safety depends on LLM training data, not on explicit validation logic, making it non-auditable under EU AI Act conformity assessment requirements.

### E. Article 17 — Quality Management System

#### FM11: QMS Silent Failure (Single Submission)

*Addressing RQ3.*

We configured an isolated backend instance with `WARDEN_LLM=mistral` and `MISTRAL_API_KEY=INVALID_KEY_FOR_FM11_TEST`, then submitted a gate justification. The execution path in `backend/main.py`:

1. `requests.post()` to `api.mistral.ai` → HTTP 401 Unauthorized → `{"detail":"Unauthorized"}`
2. `resp.raise_for_status()` raises `HTTPError`
3. Caught by `except Exception as exc:` at line 545
4. `fallback_msg = f"Response parsing failed: {raw_text}"` — embeds the 401 error string
5. Returns `{"approved": False, "score": 0, "model": "mistral-small-2506", ...}`
6. `gate_submit()` sees no `http_error` key → writes audit entry → returns HTTP 200

The gate client received HTTP 200, `decision: REJECTED`, `score: 0/100`. The only signal of failure is the string `{"detail":"Unauthorized"}` buried in the `reasoning_trace` field — an internal API error message that no compliance monitoring specification would flag as an anomaly.

Two concurrent silent failure paths exist: (1) invalid `WARDEN_LLM` API key, caught by `except Exception`; (2) Bedrock unavailable (boto3 import error in production mode), which follows the same catch-and-return path. Article 17(1g) requires a documented process for detecting and reporting serious incidents and malfunctions. A malfunction that returns HTTP 200 is not detectable by the client without parsing the free-text reasoning trace field, which is not a machine-readable error channel.

#### Finding 1/Gap 11: QMS Silent Failure Across All Nine Justification Quality Levels

*Addressing RQ3 — the primary Article 17 finding.*

We extended FM11 across all nine justification quality levels used in the justification quality test suite: three WEAK (W1–W3), three MEDIUM (M1–M3), and three STRONG (S1–S3). Each was submitted to an isolated backend with invalid credentials following a LOW_DRIFT pre-commit and HIGH_DRIFT commit cycle to ensure gate re-arming between submissions.

**Table IV. QMS Silent Failure — All Nine Quality Levels**

| ID | Category | Justification (summary) | Score (valid key) | Score (invalid key) | Verdict (invalid) | Verification Hash |
|----|----------|------------------------|-------------------|---------------------|-------------------|------------------|
| W1 | WEAK | "ok" | 20/100 | 0/100 | REJECTED | 101715c4ae103492 |
| W2 | WEAK | "approved" | 85/100 APPROVED | 0/100 | REJECTED | 68d8197f0cf4e10f |
| W3 | WEAK | "I updated the code" | 30/100 | 0/100 | REJECTED | c3b1a9f373322149 |
| M1 | MEDIUM | Vague performance claim | 30/100 | 0/100 | REJECTED | 8bedb5586a789177 |
| M2 | MEDIUM | Vague configuration update | 30/100 | 0/100 | REJECTED | 9fe0c891e236dc6c |
| M3 | MEDIUM | Vague refactoring claim | 30/100 | 0/100 | REJECTED | 11fea41af441772d |
| S1 | STRONG | SHA-256 to bcrypt migration, ticket SEC-441, ARCH-289 | 85/100 APPROVED | 0/100 | REJECTED | 01d3c114b9310639 |
| S2 | STRONG | Async DB pattern, INTENT-003, ARCH-289 | 85/100 APPROVED | 0/100 | REJECTED | 646dde230ade93a2 |
| S3 | STRONG | OAuth2, GDPR Art. 7, legal sign-off 2026-06-15 | 85/100 APPROVED | 0/100 | REJECTED | 48f8627d77b724ca |

All nine submissions return score 0/100 REJECTED with a unique verification hash. The audit trail contains nine complete records, each indistinguishable from a legitimate low-quality rejection. Contrast: with a valid key, W2 and all three STRONG justifications (S1–S3) are APPROVED (85/100); with invalid credentials all six are REJECTED (0/100).

The verification hashes confirm that each submission was independently processed — the audit trail mechanism is functioning at the record-creation level. However, the audit trail's semantic content is governance fiction: no LLM evaluation occurred for any of the nine submissions. A compliance officer auditing these records would observe nine consecutive rejections, assess the batch as low-quality justifications correctly handled by the gate, and close the review. The actual state — nine governance evaluation failures — is invisible without examining the `reasoning_trace` field for an embedded API error string.

This is the most severe Article 17 finding in this study. The QMS is designed to detect and surface AI system malfunctions; instead, it actively conceals them by generating plausible-looking audit records.

### F. Article 50 — AI System Disclosure

#### FM12/Gap 12: Article 50 Disclosure Gap

*Addressing RQ1.*

We examined the HTTP response from a successful gate submission (APPROVED, strong justification, valid credentials). The response headers were: `date`, `server: uvicorn`, `content-length`, `content-type: application/json`. No AI-specific disclosure header was present.

The JSON response body included the field `"model": "mistral-small-2506"`, which discloses AI involvement to a developer reading the response body. However, Article 50(1) requires disclosure "in a timely, clear, and intelligible manner" to natural persons. A CI/CD pipeline integration, compliance monitoring proxy, or audit logging middleware cannot intercept AI-generated decisions without parsing JSON response bodies. A standard HTTP header — `X-AI-Decision-Model: mistral-small-2506` or `X-AI-System-Involved: true` — would enable machine-readable disclosure at the protocol layer.

This finding is classified as **PARTIAL COMPLIANCE**: the `model` field in the response body constitutes disclosure for human-readable API consumers, but the absence of a machine-readable header constitutes a gap for programmatic consumers integrated into automated pipelines.

---

## VI. Discussion

### A. Three Systemic Failure Patterns

The twelve findings organise into three systemic patterns that cut across individual EU AI Act articles.

**Pattern 1: Silent QMS Failure (FM11, Finding 1/Gap 11).** Two findings address the same underlying code path — the `except Exception` catch in `_warden_llm_analyze()` — at different scales. FM11 demonstrates it for a single submission; Finding 1/Gap 11 demonstrates it collapses all nine quality levels identically. The common structure is: LLM infrastructure failure → HTTP 200 REJECTED → plausible audit record → invisible to compliance review. The minimal code fix is known (check `resp.status_code` before `raise_for_status()` and return `{"http_error": ...}` for 4xx), but its absence reveals a design assumption that the LLM backend is always available — an assumption that Article 17 specifically requires to be stress-tested.

**Pattern 2: Governance Blindspots (Finding 3, Gap 7, FM5).** Three findings involve categories of events that the system structurally cannot record. New file additions were invisible to the historical `--diff-filter=M` implementation (Finding 3). High-drift commits during engine downtime are invisible because the system has no event queue or backlog scan (Gap 7). Near-miss commits below the threshold are invisible because the audit path is only opened by gate submissions (FM5). Each blindspot is a different architectural decision; together they characterise a system designed around the nominal case (threshold-crossing commit, engine running, single commit in isolation) that does not account for the full operational envelope.

**Pattern 3: Social Engineering Surfaces (FM1, FM3, FM10/Gap 10, and the W2 finding).** Multiple findings demonstrate that the gate's effectiveness depends on untestable assumptions: that submitters are who they claim to be (FM1), that the spec vault has not been modified (FM3), that the LLM's training data covers the technical domain of the justification (FM10/Gap 10), and that the LLM does not treat approval-signalling keywords as compliance indicators (W2).

### B. The W2 Keyword Bypass Finding

A notable secondary finding from the justification quality test suite: the single word *"approved"* (justification W2) was scored **85/100 APPROVED** by `mistral-small-2506` with `temperature=0` — identically to a detailed engineering justification with ticket number, regulation reference, and sign-off date. The model appears to interpret the word as a compliance signal rather than as a content-free string. This behaviour is fully deterministic (temperature=0, same score across all runs) and was not exhibited by the prior model version (`mistral-small-2412`, which scored W2 at 0/100 REJECTED).

This finding illustrates a general vulnerability in LLM-as-judge architectures: the evaluator may respond to surface features (approval-signalling keywords) rather than content quality, and this behaviour can change silently between model versions. The behaviour is version-specific and therefore not foreseeable without empirical testing of each model release.

### C. The Conditional Mitigation and Auditable Validation

FM10/Gap 10 (MITIGATED) raises a broader question about what constitutes auditable compliance validation. The gate detected the MD5/bcrypt error incidentally — Mistral's training data happened to include documentation of this well-known vulnerability. This is not the same as the gate having been designed to perform technical validation. An EU AI Act conformity assessment requires providers to demonstrate that their controls work for a stated reason, not that they produce correct outputs in specific test cases for incidental reasons. A control whose effectiveness depends on unpublished, unverifiable LLM training data coverage cannot be formally audited.

### D. Multi-LLM Comparison as Future Work

All findings in this study were produced using a single LLM backend (`mistral-small-2506`). It is not known whether FM10/Gap 10 would remain MITIGATED with a different model, whether W2 (keyword bypass) is specific to `mistral-small-2506` or general, or whether the score ranges for FM1 and other LLM-evaluated findings would shift under a different provider. A systematic multi-LLM comparison study — repeating the full test suite with at least three distinct models (e.g., Gemini, Llama, and GPT-4o) — is planned as future work. Such a study would allow characterisation of which findings are model-specific vulnerabilities and which are architectural vulnerabilities independent of the LLM backend.

---

## VII. Threats to Validity

### A. Internal Validity

The test suite uses real git commits against a live backend. Commit ordering, drift threshold setting, and gate state at test initiation are controlled via the test harness. However, the gate state machine is in-memory only; an unexpected backend crash during testing could produce inconsistent results. We mitigated this by restarting the backend to a known CLEAR state before each test.

FM1 score variance (40–45/100 across runs) despite temperature=0 is attributable to gate context: the LLM's calibration is influenced by prior gate submissions in the same test session, which affect session-level context. This is an internal validity concern for LLM-as-judge evaluations more generally [4].

### B. External Validity

The Spec-Drift Chronometer is a single production system. Findings about its gate implementation (FM11, Finding 1/Gap 11) may not generalise to other HITL gate architectures. However, the underlying failure pattern — an unchecked `except Exception` in the LLM call path returning a plausible negative decision — is a general design antipattern applicable to any system using a similar structure.

The FM3 specification gaming finding generalises to any system using a vocabulary-overlap scorer against a mutable reference document without access controls. This design pattern is common in early-stage governance tooling.

### C. Construct Validity

The drift threshold (0.0075) is a configurable parameter. A higher or lower threshold would change which findings triggered the gate and which did not (particularly FM5). Our findings are reported at the system's configured threshold; the structural findings (FM1, FM3, Finding 3, Gap 7, FM11, Finding 1/Gap 11) are threshold-independent.

The LLM judge's scores are constructed measurements. As the W2 finding demonstrates, LLM judges may respond to surface features rather than content quality. All findings involving LLM scores should be interpreted as measurements of the specific model's behaviour on the specific prompt, not as ground-truth quality assessments.

### D. Conclusion Validity

The test suite was executed once from a fresh clone. For findings with score variance (FM1: 40–45/100), we report the observed range. For findings that are fully deterministic (temperature=0, no LLM involved), a single run is sufficient. We note that the nine verification hashes in Table IV provide a content-addressable fingerprint that any independent verifier can reproduce to confirm that specific submissions produced specific audit records.

---

## VIII. Conclusion

This paper presented a structured empirical study of twelve failure modes and compliance gaps in a production EU AI Act governance system. Across EU AI Act Articles 9, 12, 13, 14, 17, and 50, we confirmed nine failure modes, conditionally mitigated one, and identified one partial compliance finding. The three systemic patterns — silent QMS failure, governance blindspots, and social engineering surfaces — represent failure categories that are likely to recur across EU AI Act compliance implementations because they arise from common design assumptions (LLM backends are always available; specification documents are trusted and controlled; gate endpoints are accessed only by authorised actors) rather than system-specific bugs.

The most severe finding is Finding 1/Gap 11: a QMS silent failure that generates nine plausible audit records across all justification quality levels, each with a unique verification hash, during a period when no LLM evaluation occurred. This finding demonstrates that audit trail completeness is a necessary but not sufficient condition for audit trail validity under Article 17. A functioning QMS must distinguish between a legitimate REJECTED decision and a governance evaluation failure — a capability the current system lacks.

The conditional mitigation in FM10/Gap 10 illustrates a broader challenge for EU AI Act conformity assessment: when a compliance control's effectiveness depends on the implicit knowledge embedded in an LLM's training data, that effectiveness cannot be audited through any means other than empirical testing across a broad range of test cases. This creates a structural tension between the Act's auditability requirements and the opacity of current LLM training processes.

A multi-LLM comparison study is planned as future work to determine which of these findings are model-specific and which are architectural, and to assess whether findings such as the W2 keyword bypass are general vulnerabilities in LLM-based justification evaluation or artefacts of specific model versions.

All test scripts, results, and data are publicly available for independent reproduction at: https://github.com/VinitaSilaparasetty/spec-drift_chronometer

---

## Acknowledgements

The research design, empirical test suite, system architecture, data collection, and analysis in this manuscript constitute the original intellectual work of the author. Manuscript drafting assistance was provided by Claude (Anthropic), an AI language model. All test data, findings, interpretations, and conclusions were produced and verified by the author. Use of AI for drafting is disclosed in accordance with the editorial policies of IEEE publications and the spirit of EU AI Act Article 50.

---

## References

[1] European Parliament and Council of the European Union, "Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act) and amending certain Union legislative acts," *Official Journal of the European Union*, vol. L 2024/1689, Jul. 2024. [Online]. Available: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689

[2] A. Q. Jiang, A. Sablayrolles, A. Mensch, C. Bamford, D. S. Chaplot, D. de las Casas, F. Bressand, G. Lengyel, G. Lample, L. Saulnier, L. R. Lavaud, M.-A. Lachaux, P. Stock, T. Le Scao, T. Lavril, T. Wang, T. Lacroix, and W. El Sayed, "Mistral 7B," *arXiv preprint arXiv:2310.06825*, 2023.

[3] International Organization for Standardization, "ISO/IEC 42001:2023 — Information technology — Artificial intelligence — Management system," ISO, Geneva, Switzerland, 2023.

[4] L. Zheng, W.-L. Chiang, Y. Sheng, S. Zhuang, Z. Wu, Y. Zhuang, Z. Li, D. Li, E. P. Xing, H. Zhang, J. E. Gonzalez, and I. Stoica, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," in *Proc. 37th Conf. Neural Information Processing Systems (NeurIPS)*, New Orleans, LA, Dec. 2023.

[5] S. Amershi, A. Begel, C. Bird, R. DeLine, H. Gall, E. Kamar, N. Nagappan, B. Nushi, and T. Zimmermann, "Software engineering for machine learning: A case study," in *Proc. 41st Int. Conf. Software Engineering: Software Engineering in Practice (ICSE-SEIP)*, Montreal, QC, May 2019, pp. 291–300.

[6] M. Veale and F. Z. Borgesius, "Demystifying the draft EU Artificial Intelligence Act," *Computer Law Review International*, vol. 22, no. 4, pp. 97–112, 2021.

[7] P. Hacker, A. Engel, and M. Mauer, "Regulating ChatGPT and other large language models: Opportunities and challenges," in *Proc. 2023 ACM Conf. Fairness, Accountability, and Transparency (FAccT '23)*, Chicago, IL, Jun. 2023, pp. 1–12.

[8] R. Wieringa, *Design Science Methodology for Information Systems and Software Engineering*. Berlin, Germany: Springer, 2014.

[9] Y. Chang, X. Wang, J. Wang, Y. Wu, L. Yang, K. Zhu, H. Chen, X. Yi, C. Wang, Y. Wang, W. Ye, Y. Zhang, Y. Chang, P. S. Yu, Q. Yang, and X. Xie, "A survey on evaluation of large language models," *ACM Trans. Intelligent Systems and Technology*, vol. 15, no. 3, pp. 1–45, Mar. 2024.

[10] R. Bommasani, D. A. Hudson, E. Aditi, R. Altman, S. Arora, S. Borber, et al., "On the opportunities and risks of foundation models," *arXiv preprint arXiv:2108.07258*, Stanford Center for Research on Foundation Models, 2021.

[11] IEEE Standards Association, "IEEE Std 730-2014: IEEE Standard for Software Quality Assurance Processes," IEEE, New York, NY, 2014.

[12] G. J. Myers, C. Sandler, and T. Badgett, *The Art of Software Testing*, 3rd ed. Hoboken, NJ: Wiley, 2011.

[13] X. Wang and H. Yu, "How to break MD5 and other hash functions," in *Proc. EUROCRYPT 2005*, vol. 3494, Lecture Notes in Computer Science. Berlin, Heidelberg: Springer, 2005, pp. 19–35.

[14] D. Sculley, G. Holt, D. Golovin, E. Davydov, T. Phillips, D. Ebner, V. Chaudhary, M. Young, J.-F. Crespo, and D. Dennison, "Hidden technical debt in machine learning systems," in *Proc. 28th Conf. Neural Information Processing Systems (NeurIPS)*, Montreal, QC, 2015, pp. 2503–2511.

[15] J. Wei, X. Wang, D. Schuurmans, M. Bosma, B. Ichter, F. Xia, E. Chi, Q. Le, and D. Zhou, "Chain-of-thought prompting elicits reasoning in large language models," in *Proc. 36th Conf. Neural Information Processing Systems (NeurIPS)*, New Orleans, LA, 2022.

---

*© 2026 Vinita Silaparasetty, Aevoxis Solutions. Manuscript ID: AEVOXIS-WE-MS-2026-001. All rights reserved. Unauthorized reproduction prohibited.*
