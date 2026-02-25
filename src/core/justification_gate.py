import sys
import json
import datetime
# Internal import adjusted for the new 'core' directory structure
from warden_brain import WardenSwarm

def ai_heal_documentation(warden, justification, diff):
    """
    Phase 4: AI-Healing Pipeline.
    Synchronizes architectural drift with design.md using Nova Lite.
    """
    try:
        design_path = "design.md"
        current_design = ""
        try:
            with open(design_path, "r") as f:
                current_design = f.read()
        except FileNotFoundError:
            current_design = "# Spec-Drift Chronometer Design Documentation\n"
        
        prompt = f"""
        UPDATE MISSION: Integrate this human justification into the existing design.md.
        Existing Design: {current_design}
        New Justification: {justification}
        Affected Code Diff: {diff}
        
        Output the updated design.md content only. Maintain professional German Engineering standards.
        """
        
        # Invoke Nova Lite via Amazon Bedrock (Sovereign Infrastructure in eu-central-1)
        response = warden.bedrock.invoke_model(
            modelId=warden.lite_model,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            })
        )
        res_body = json.loads(response['body'].read())
        updated_content = res_body['content'][0]['text']
        
        with open(design_path, "w") as f:
            f.write(updated_content)
        return True
    except Exception as e:
        print(f"[ERROR] AI-Healing failed: {e}")
        return False

def run_gate():
    """
    The Enforcement Gate: Article 14 Human Oversight check.
    """
    warden = WardenSwarm()
    diff = warden.capture_diff()
    
    if not diff or "No changes detected" in diff:
        print("[SYSTEM] No architectural drift detected. Gate standing down.")
        return

    print("\n🚨 [EU AI ACT COMPLIANCE GATE] 🚨")
    print("Architectural Drift detected in Germany (eu-central-1).")
    print("Complete the Sovereign Compliance Checklist (Art. 10, 13, 14):")
    
    check_1 = input("[ ] Art 10: Is data quality and governance maintained? (y/n): ")
    check_2 = input("[ ] Art 13: Is the change transparent and documented? (y/n): ")
    check_3 = input("[ ] Art 14: Do you accept full liability for this change? (y/n): ")
    
    if not all(c.lower() == 'y' for c in [check_1, check_2, check_3]):
        print("\n❌ ACCESS DENIED: Compliance Checklist incomplete. Operation aborted.")
        sys.exit(1)

    justification = input("\nPROMPT: Provide technical justification for the Audit Trail: ")
    
    if len(justification) < 15:
        print("❌ REJECTED: Justification too vague. Minimum 15 characters required.")
        sys.exit(1)

    print("\n[SYSTEM] Logging to DynamoDB & Triggering AI-Healing Pipeline...")
    
    # 1. Log to Cloud Ledger (EU AI Act Article 12: Traceability)
    incident_id = f"COMPLIANCE_{int(datetime.datetime.now().timestamp())}"
    warden.table.put_item(Item={
        'IncidentID': incident_id,
        'Timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
        'Justification': justification,
        'ComplianceCheck': "ART_10_13_14_PASSED",
        'VerificationHash': warden.generate_verification_hash(diff),
        'Region': 'eu-central-1'
    })

    # 2. AI-Healing (Autonomous Documentation Sync)
    if ai_heal_documentation(warden, justification, diff):
        print("✅ MISSION COMPLETE: design.md has been self-healed via Nova Lite.")
    else:
        print("⚠️  Warning: Cloud log saved but local documentation sync failed.")

if __name__ == "__main__":
    run_gate()
