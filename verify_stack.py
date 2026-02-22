import os
import json
import subprocess

def check_structure():
    print("--- 1. Path Integrity Check ---")
    files = [
        ".kiro/steering/tech.md", 
        ".kiro/steering/spec.json", 
        "requirements.md", 
        "infra/dynamodb_schema.json"
    ]
    all_pass = True
    for f in files:
        exists = os.path.exists(f)
        status = "PASS" if exists else "FAIL"
        if not exists: all_pass = False
        print(f"[{status}] {f}")
    return all_pass

def check_aws_connectivity():
    print("\n--- 2. Cloud Connectivity Check ---")
    try:
        # Check if the table we created is actually reachable
        result = subprocess.run(
            ["aws", "dynamodb", "describe-table", "--table-name", "SpecDrift_Ledger", "--query", "Table.TableStatus", "--output", "text"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            status = result.stdout.strip()
            print(f"[PASS] DynamoDB 'SpecDrift_Ledger' is {status}")
            return True
        else:
            print(f"[FAIL] Could not reach DynamoDB. Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] AWS CLI not responding: {e}")
        return False

if __name__ == "__main__":
    print("--- Running Sovereign Health Check (Enhanced) ---")
    struct_ok = check_structure()
    cloud_ok = check_aws_connectivity()
    
    if struct_ok and cloud_ok:
        print("\n[RESULT] SYSTEM STATUS: OPERATIONAL (Phase 1 Complete)")
    else:
        print("\n[RESULT] SYSTEM STATUS: DEGRADED (Check errors above)")
