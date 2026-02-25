import os
import subprocess

def check_system():
    print("--- 1. Path Integrity Check ---")
    # Verifying the core sovereign files are present
    files = [".kiro/steering/tech.md", ".kiro/steering/spec.json", "requirements.md"]
    for f in files:
        status = "PASS" if os.path.exists(f) else "FAIL"
        print(f"[{status}] {f}")

    print("\n--- 2. Cloud Connectivity Check ---")
    # Verifying the DynamoDB Ledger is reachable in eu-central-1
    result = subprocess.run(["aws", "dynamodb", "describe-table", "--table-name", "SpecDrift_Ledger", "--query", "Table.TableStatus", "--output", "text"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[PASS] DynamoDB 'SpecDrift_Ledger' is {result.stdout.strip()}")
    else:
        print("[FAIL] Could not reach DynamoDB. Ensure AWS CLI is configured for eu-central-1.")

if __name__ == "__main__":
    print("--- Running Sovereign Health Check ---")
    check_system()
