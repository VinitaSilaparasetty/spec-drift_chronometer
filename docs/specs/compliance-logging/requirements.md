# REQ-AUD-001: Intent Ledger Logging

## Specification
- **Trigger**: WHEN an agent proposes a code change.
- **Precondition**: IF the change deviates from the "Active Spec Memory" or architectural constraints.
- **Action**: The system SHALL record the justification and the delta in the DynamoDB Intent Ledger.

## Acceptance Criteria
1. Logs must capture the "Negotiation" between the Coder and Warden agents.
2. Must follow the Structured-JSON-Logging pattern.
3. Implementation must be strictly asynchronous to avoid IDE lag.
