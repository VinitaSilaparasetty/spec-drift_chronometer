# Technology Stack & Constraints (Governed)

## 1. Core Environment
- **Runtime**: Python 3.12+
- **Dependency Management**: uv / uvx
- **Cloud Infrastructure**: AWS Serverless (Free Tier Optimized)
- **AI Orchestration**: Amazon Bedrock AgentCore & Strands SDK

## 2. Behavioral Requirements (EARS)

### REQ-TECH-001: Runtime Enforcement
- **Trigger**: WHEN the system is initialized or deployed.
- **Action**: The system SHALL verify the Python version is >= 3.12.

### REQ-TECH-002: Infrastructure Provisioning
- **Trigger**: WHEN a infrastructure update is detected.
- **Precondition**: IF the change affects the Intent Ledger.
- **Action**: The system SHALL use the AWS CLI or CDK to reconcile the 'SpecDrift_Ledger' against infra/dynamodb_schema.json.

### REQ-TECH-003: Agent Communication
- **Trigger**: WHEN the Coder Agent proposes a code modification.
- **Precondition**: IF the change violates the Architectural Baseline.
- **Action**: The system SHALL trigger the Warden via the Strands SDK to intercept the process.

### REQ-TECH-004: Audit Logging (Article 12)
- **Trigger**: WHEN any governance event or "Kill Switch" is activated.
- **Action**: The system SHALL emit a Structured JSON log to the Intent Ledger via ledger_client.py.

### REQ-TECH-005: Language Constraint
- **Trigger**: WHEN a new file or dependency is proposed.
- **Precondition**: IF the proposed language is not Python.
- **Action**: The system SHALL reject the proposal and log a "Non-Standard Language" violation.
