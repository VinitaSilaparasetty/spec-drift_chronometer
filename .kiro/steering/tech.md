# Technology Stack & Constraints
## Core Languages & Tools
- **Language**: Python 3.12+ (Strict)
- **Package Manager**: uv / uvx (Mandatory for all MCP servers)
- **Cloud**: AWS (Bedrock, Boto3 SDK)

## Technical Constraints
- **NO NPM/NODE**: Do not suggest or use Node.js, npm, or npx for backend or MCP logic.
- **MCP Integration**: Use only the verified Python-based servers via uvx.
- **Logging**: Use structured JSON logging to facilitate audit trails for German compliance.
- **Testing**: Pytest for unit and integration tests.
