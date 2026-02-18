# Technology Stack & Constraints (EARS-Compliant)

## Core Stack
- **Language**: Python 3.12+
- **Package Manager**: uv / uvx
- **Cloud Infrastructure**: AWS (Bedrock, Boto3, DynamoDB)

## Technical Requirements (EARS)

### REQ-ENV-001: Environment Consistency
WHEN a new environment is initialized, IF MCP servers are required, the system SHALL utilize uvx exclusively for installation and execution.

### REQ-ENV-002: Technology Exclusion
WHEN suggesting libraries or tools, IF the solution involves backend or MCP logic, the system SHALL NOT utilize Node.js, npm, or npx.

### REQ-AUD-001: Structured Logging
WHEN any core function executes, IF state is modified, the system SHALL emit structured JSON logs to satisfy German compliance audit trails.

### REQ-TEST-001: Testing Framework
WHEN automated tests are executed, the system SHALL utilize pytest.
