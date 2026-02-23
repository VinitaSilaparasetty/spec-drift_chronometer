# Technology Stack & Constraints (Unified Sovereign Version)

## 1. Core Environment
* **Runtime:** Python 3.12+
* **Dependency Management:** uv / uvx
* **Cloud Infrastructure:** AWS (Bedrock, Boto3, DynamoDB)
* **AI Orchestration:** Amazon Bedrock AgentCore & Strands SDK

## 2. Universal Constraints (MANDATORY)
* **Logic Constraint:** All AI logic must utilize the Strands SDK and Bedrock AgentCore exclusively.
* **Audit Constraint:** All architectural checks must reference and log to the Intent Ledger in DynamoDB.

## 3. Behavioral Requirements (EARS)

**REQ-TECH-001: Runtime & Environment**
* **Trigger:** WHEN the system is initialized or deployed.
* **Action:** The system SHALL verify Python version >= 3.12 and utilize uvx exclusively for MCP installation.

**REQ-TECH-002: Technology Exclusion**
* **Trigger:** WHEN suggesting libraries or tools.
* **Precondition:** IF the solution involves backend or MCP logic.
* **Action:** The system SHALL NOT utilize Node.js, npm, or npx.

**REQ-TECH-003: Agent Communication & Validation**
* **Trigger:** WHEN the Coder Agent proposes a code modification.
* **Precondition:** IF the change violates the Architectural Baseline.
* **Action:** The system SHALL use the Strands SDK to trigger the Warden to intercept, validate the change, and reference the DynamoDB Intent Ledger.

**REQ-LOG-004: Immutable Audit Trail**
* **Trigger:** WHEN the Warden syncs laws to the Cloud.
* **Action:** The system SHALL generate a SHA-256 VerificationHash and include ModelFingerprint and ReasoningTrace metadata in the DynamoDB entry.
