# Boilerplate Standards
- Whenever a new file is created in `src/`, apply this header: `/* (c) 2026 Aevoxis - Spec-Drift Chronometer */`
- DO NOT generate logic unless I provide a specific #requirements tag.
- If a file is empty, automatically scaffold the standard imports for the  AWS/Python stack:
  ```python
  import boto3
  import json
  import os
  from mcp_server_fetch import FetchServer
  ```
