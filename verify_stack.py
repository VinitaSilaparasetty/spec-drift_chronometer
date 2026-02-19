import os
import json

def check_structure():
    files = [".kiro/steering/tech.md", ".kiro/steering/spec.json", "requirements.md", "infra/dynamodb_schema.json"]
    for f in files:
        status = "PASS" if os.path.exists(f) else "FAIL"
        print(f"[{status}] {f}")

if __name__ == "__main__":
    print("--- Running Sovereign Health Check ---")
    check_structure()
