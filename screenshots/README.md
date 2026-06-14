# Spec-Drift Chronometer — UI Screenshots

Screenshots are generated automatically when the app runs. Below are detailed
descriptions of each screen so you know what to expect.

---

## Screen 1 — Sovereign Dashboard (baseline state)

**File:** `01-dashboard-sovereign.png`

The main dashboard loads on a pure black (`#000000`) background with the title
"Spec-Drift **Chronometer**" in large italic/bold type, followed by the subtitle
"Aevoxis Governance Layer // EU AI Act Art. 12 & 14 Compliant."

A small amber badge reading **DEMO MODE** appears next to the subtitle.

**Four stat cards** (dark zinc-900 tiles) span the top:
| Card | Value (baseline) | Color |
|------|-----------------|-------|
| System Health | SOVEREIGN | Emerald green |
| Drift Index | 0.0011 | Blue |
| Spec Compliance | 100% | Emerald green |
| Warden Status | Observing | Amber |

Below the cards, a **drift variance bar chart** shows 20 narrow vertical bars.
In the sovereign phase each bar is short and emerald-green, well below the amber
dashed horizontal line that marks the sovereign threshold (0.0075).

To the right of the chart, the **Warden Activity Log** shows timestamped entries
like `[10:21:43] SEC_AUDIT_PASS: Drift 0.0011 within sovereign limits.`

Below the log, the **Sovereign Spec Vault** panel lists the five `.kiro/steering/`
files with ACTIVE / LOCKED status badges.

At the bottom of the chart panel, two buttons: **Run Audit** (amber) and
**Download Audit** (zinc-gray).

---

## Screen 2 — Justification Gate (critical drift state)

**File:** `02-justification-gate.png`

After ~45 seconds in DEMO_MODE, the drift crosses 0.0075. The header bar gains
a pulsing red button reading **JUSTIFICATION GATE ACTIVE**. The Drift Index card
turns red and shows a value like `0.0099`. The System Health card shows
**CRITICAL_DRIFT** in red. The Spec Compliance card shows **BREACH** in red.

A **full-screen overlay** (80% black, blurred backdrop) appears with a modal titled:

> **Justification Gate — ACTIVE**
> EU AI Act Article 14 · Human-in-the-Loop Required

Inside the modal:
- A three-column metric row shows **Drift Detected** (red, e.g. `0.0099`),
  **Sovereign Threshold** (gray, `0.0075`), and **Excess Delta** (amber, e.g. `+0.0024`).
- A spec reference line points to `.kiro/steering/tech.md §2` and the model `amazon.nova-pro-v1:0`.
- A multi-line textarea with placeholder text explains what kind of justification to write.
- An amber **Submit to Warden Agent** button.

---

## Screen 3 — Justification Gate (resolved — APPROVED)

**File:** `03-gate-approved.png`

After the user types a justification and clicks Submit:

1. The button becomes "Warden Analyzing..." with a pulsing amber dot and the text
   "Invoking amazon.nova-pro-v1:0 in eu-central-1 for reasoning analysis..."
2. After ~1 second (DEMO_MODE), the modal updates to show the header in emerald:
   **Justification Gate — APPROVED**
3. An emerald badge shows **APPROVED** alongside the model fingerprint and SHA-256 hash.
4. The **Warden Reasoning Trace** pre-formatted block shows the full Nova Pro analysis,
   including Intent Alignment Score (91/100), cross-references to governance docs, and
   the final "APPROVED" decision line.
5. A "Close Gate — Return to Dashboard" button in zinc-gray closes the overlay.

Back on the dashboard, the Warden Activity Log now shows:
`[NOW] GATE RESOLVED: APPROVED. Drift event logged to audit trail.`

---

## Screen 4 — Audit Trail Download

**File:** `04-audit-trail.png`

After clicking **Download Audit**, the browser downloads `spec_drift_audit_trail.txt`.
The file contains an ASCII-framed report:

```
╔══════════════════════════════════════════════════════════════╗
║      SPEC-DRIFT CHRONOMETER — SOVEREIGN AUDIT TRAIL         ║
╚══════════════════════════════════════════════════════════════╝

Timestamp:          2026-03-12 11:21:00 UTC
Mode:               DEMO_MODE (simulated)
Drift Index:        0.0099
Threshold:          0.0075
Gate Status:        RESOLVED
...
── GOVERNANCE COMPLIANCE ──────────────────────────────────────
EU AI Act Article 14 (Human Oversight):   VERIFIED
EU AI Act Article 12 (Transparency):      VERIFIED
Sovereign Region:                          eu-central-1 (Frankfurt)
System Integrity:                          100%

── JUSTIFICATION GATE RECORD ──────────────────────────────────
Decision:         APPROVED
Justification:    <user's text>
══════════════════════════════════════════════════════════════
```
