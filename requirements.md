# Technical Requirements: Spec-Drift Chronometer

## 1. Intent Ledger (Phase 1: Persistence)
- **REQ-INT-001**: The system SHALL initialize a **DynamoDB** table named 'SpecDrift_Ledger' using the AWS Free Tier.
- **REQ-INT-002**: Every architectural decision intercepted by the **Justification Gate** SHALL be stored as a versioned JSON item.
- **REQ-INT-003**: The Ledger SHALL store the Partition Key (`ProjectID`) and Sort Key (`Timestamp#IntentID`).

## 2. Audit & Negotiation (Phase 2: Recording)
- **REQ-AUD-001**: Intent Ledger Logging
    - **Trigger**: WHEN an agent proposes a code change.
    - **Precondition**: IF the change deviates from the "Active Spec Memory" or architectural constraints.
    - **Action**: The system SHALL record the justification and the code delta in the 'SpecDrift_Ledger'.
    - **Constraint**: Logs MUST follow the Structured-JSON-Logging pattern for Article 12 compliance.

## 3. Semantic Drift Detection (Phase 3: Intelligence)
- **REQ-DRIFT-001**: The system SHALL use **Amazon Nova Lite** to scan for semantic deviations between active code and this requirements file.
- **REQ-DRIFT-002**: IF a deviation is detected, THEN the system SHALL generate a Non-Compliance Report (NCR) for the Warden.

## 4. Justification Gate & Warden (Phase 4: Enforcement)
- **REQ-GOV-001**: The **Warden Agent** SHALL intercept all "vibe-coding" attempts that lack a corresponding entry in the Intent Ledger.
- **REQ-GOV-002**: The system SHALL provide a **Sovereign Override** (Kill Switch) that allows the human to terminate all agentic negotiations immediately.
- **REQ-GOV-003**: The Warden SHALL satisfy **EU AI Act Article 14** by requiring explicit human-in-the-loop approval for all high-risk drift overrides.
