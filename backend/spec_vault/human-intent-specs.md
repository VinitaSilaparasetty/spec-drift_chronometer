# Human Intent Specifications — Sovereign Architect Declarations

> This file contains the explicit, human-authored architectural decisions that the
> Warden Engine uses as the ground-truth baseline for drift detection. Any AI-generated
> code that deviates from these declarations triggers the Justification Gate.
>
> Last verified by: Vinita Silaparasetty
> Verification date: 2026-03-12
> Status: ACTIVE — EU AI Act Article 14 compliant

---

## INTENT-001 · Data Residency

**Declaration:** All persistent data (DynamoDB tables, S3 buckets, Bedrock model invocations)
MUST reside in `eu-central-1` (Frankfurt). No data may be written to any other AWS region.

**Rationale:** GDPR Article 44 data transfer restrictions and EU AI Act Article 10 data
governance requirements. We committed this to our legal team on 2026-01-15.

**Warden behaviour:** Reject any infrastructure change that specifies a region other than
`eu-central-1`. Trigger Justification Gate if an alternative region is proposed.

---

## INTENT-002 · AI Model Hierarchy

**Declaration:** The primary reasoning model is `amazon.nova-pro-v1:0`. The fallback for
latency-sensitive paths is `amazon.nova-lite-v1:0`. No other models are permitted.

**Rationale:** Nova Pro provides the reasoning depth required for EU AI Act Article 13
(Transparency) compliance. Nova Lite maintains sub-200ms latency for the heartbeat loop.

**Warden behaviour:** Reject any code that imports or invokes a Bedrock model ID not in
`["amazon.nova-pro-v1:0", "amazon.nova-lite-v1:0"]`.

---

## INTENT-003 · Human-in-the-Loop Gate

**Declaration:** The Justification Gate (Article 14 Human Oversight mechanism) MUST be
invocable for every drift event that exceeds `semantic_drift_threshold: 0.15`. The gate
must block automated merges until a human justification is recorded.

**Rationale:** EU AI Act Article 14 requires that high-risk AI systems allow humans to
intervene and override outputs. Our system is classified as high-risk under Annex III.

**Warden behaviour:** If a code change disables, bypasses, or weakens the Justification Gate
logic, immediately halt and require a `SOVEREIGN OVERRIDE` signed by the architect.

---

## INTENT-004 · Audit Trail Immutability

**Declaration:** Every Justification Gate decision MUST be written to the Intent Ledger
(DynamoDB or local `.kiro/audit/` in DEMO_MODE) with:
  - UTC timestamp
  - drift_value at time of trigger
  - human justification text
  - Warden AI reasoning trace
  - SHA-256 verification hash
  - model fingerprint

**Rationale:** EU AI Act Article 12 requires maintaining detailed logs for post-hoc auditing
by regulatory bodies. Records must be retained for a minimum of 10 years.

**Warden behaviour:** Reject any change that removes fields from the audit schema or that
writes audit records without the verification hash.

---

## INTENT-005 · Dependency Policy

**Declaration:** Backend core logic (anything in `backend/`) MUST use Python only.
No Node.js, TypeScript, or Bun may be used in the backend execution path.

**Rationale:** Lambda packaging, Python type safety, and team expertise are all aligned
on Python. Mixed runtimes increase attack surface and CI complexity.

**Warden behaviour:** Reject any backend file that contains `require()`, `import from 'node:'`,
or references to package.json scripts in the execution path.

---

## INTENT-006 · Drift Threshold

**Declaration:** The operational drift threshold is `0.0075` (configurable via
`DRIFT_THRESHOLD` env var but must not be set above `0.015` without architect approval).

**Rationale:** Empirically calibrated against our swarm dataset. Values above 0.015 indicate
catastrophic specification collapse requiring immediate halt, not just gate review.

**Warden behaviour:** Warn if `DRIFT_THRESHOLD` is configured above `0.015` and require
written justification in this file before the change is accepted.
