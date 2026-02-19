# Technical Requirements: Spec-Drift Chronometer

## 1. Intent Ledger (Phase 1)
- **REQ-INT-001**: The system SHALL initialize a **DynamoDB** table named 'SpecDrift_Ledger' using the AWS Free Tier.
- **REQ-INT-002**: Every architectural decision intercepted by the **Justification Gate** SHALL be stored as a versioned JSON item.
- **REQ-INT-003**: The Ledger SHALL store the Partition Key (ProjectID) and Sort Key (Timestamp#IntentID).

## 2. Semantic Drift Detection (Phase 2)
- **REQ-DRIFT-001**: The system SHALL use **Amazon Nova Lite** to scan for semantic deviations between active code and this requirements file.

## 3. Justification Gate & Warden (Phase 3)
- **REQ-GOV-001**: The **Warden Agent** SHALL intercept all "vibe-coding" attempts that lack a corresponding entry in the Intent Ledger.
- **REQ-GOV-002**: The system SHALL provide a **Sovereign Override** (Kill Switch) that allows the human to terminate all agentic negotiations immediately.
