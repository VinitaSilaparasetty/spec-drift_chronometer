# Boilerplate Standards: Spec-Drift Chronometer (Master Version)

## 1. Governance Headers
Whenever a new file is created in `src/`, apply this header:
/* (c) 2026 Aevoxis - Spec-Drift Chronometer */

## 2. Logic Guardrails
* DO NOT generate logic unless I provide a specific #requirements tag.
* All logic must be cross-referenced against `.kiro/steering/tech.md`.

## 3. Standard Scaffold (AWS & MCP Integration)
If a file is empty, automatically scaffold the following standard imports. Note the fail-safe for the MCP Fetch Server to ensure portability during judging:

```python
import os
import json
import boto3
from datetime import datetime

# Fail-safe for MCP (Sovereign Nervous System)
try:
    from mcp_server_fetch import FetchServer
    MCP_ENABLED = True
except ImportError:
    # Fallback to standard cloud-only mode
    MCP_ENABLED = False

# Global Compliance Constant
REGION = "eu-central-1" 
