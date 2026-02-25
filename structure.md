# Project Structure & Conventions: Spec-Drift Chronometer

## 1. Directory Map
* **`.kiro/`**: Sovereign Governance Layer. Contains steering files (`tech.md`, `governance.md`) and automation hooks.
* **`src/core/`**: The "Warden Brain." Core logic for Spec-Drift monitoring and architectural intent alignment.
* **`src/api/`**: Integration Layer. Interfaces for the MCP Fetch Server and AWS Bedrock (Nova) agents.
* **`src/utils/`**: The "Sensors." Reusable helpers for regulatory sensing, data validation, and telemetry.
* **`tests/`**: Mirror of `src/`. Contains functional and "Drift-Injection" tests.

## 2. Naming Conventions
* **Files/Folders**: `snake_case` (e.g., `intent_ledger.py`).
* **Classes**: `PascalCase` (e.g., `GovernanceWarden`).
* **Functions/Variables**: `snake_case` (e.g., `calculate_semantic_drift()`).
* **Constants**: `UPPER_SNAKE_CASE` (e.g., `SOVEREIGN_REGION = "eu-central-1"`).

## 3. Architectural Principles
* **Modular Sovereignty**: Keep core governance logic decoupled from cloud-specific SDKs. 
* **Auditability First**: Every function in `src/core/` must support a "Reasoning Trace" to satisfy EU AI Act Article 12.
* **Fail-Safe Imports**: All external dependencies (like MCP) must use `try-except` blocks to maintain system availability.
