# Technical Requirements: Spec-Drift Chronometer (Master)

## 1. Intent Ledger (Phase 1: Persistence)
- **REQ-INT-001**: The system SHALL initialize a **DynamoDB** table named 'SpecDrift_Ledger' using the AWS Free Tier.
- **REQ-INT-003**: The Ledger SHALL store the Partition Key (`IncidentID`) and Sort Key (`Timestamp`).

## 2. Audit & Negotiation (Phase 2: Recording)
- **REQ-AUD-001**: Intent Ledger Logging
    - **Trigger**: WHEN an agent proposes a code change.
    - **Precondition**: IF the change deviates from the "Active Spec Memory".
    - **Action**: The system SHALL record the justification (ReasoningTrace) and ModelFingerprint.
