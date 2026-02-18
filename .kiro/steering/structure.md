# Project Structure & Conventions
## Directory Map
- `src/core/`: Business logic for Spec-Drift monitoring and DiGA analysis.
- `src/api/`: Interfaces for MCP servers and AWS Bedrock agents.
- `src/utils/`: Reusable helper functions (image processing, data validation).
- `tests/`: Corresponding test suites mirroring the src structure.

## Naming Conventions
- **Files/Folders**: snake_case (e.g., `governance_engine.py`).
- **Classes**: PascalCase (e.g., `SpecMonitor`).
- **Functions**: snake_case (e.g., `validate_drift()`).

## Architectural Decision
- Use **Modular Design**: Keep core governance logic separate from the AWS-specific implementation to allow for multi-cloud audits.
