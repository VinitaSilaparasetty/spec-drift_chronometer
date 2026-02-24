import sys
import json
from src.warden_brain import WardenSwarm

def ai_heal_documentation(warden, justification, diff):
    """Uses Nova Lite to intelligently update design.md (The Healing Pipeline)."""
    try:
        with open("design.md", "r") as f:
            current_design = f.read()
        
        prompt = f"""
        UPDATE MISSION: Integrate this human justification into the existing design.md.
        Existing Design: {current_design}
        New Justification: {justification}
        Affected Code Diff: {diff}
        
        Output the updated design.md content only. Maintain professional German Engineering standards.
        """
        
        response = warden.bedrock.invoke_model(
            modelId=warden.lite_model,
            body=json.dumps({"messages": [{"role": "user", "content": [{"text": prompt}]}]})
        )
        res_body = json.loads(response['body'].read())
        updated_content = res_body['output']['message']['content'][0]['text']
        
        with open("design.md", "w") as f:
            f.write(updated_content)
        return True
    except Exception as e:
        print(f"[ERROR] AI-Healing failed: {e}")
        return False

def run_gate():
    warden = WardenSwarm()
    diff = warden.capture_diff()
    
    if not diff or "No changes detected" in diff:
        return

    print("\n🚨 [EU AI ACT COMPLIANCE GATE] 🚨")
    print("Architectural Drift detected. You must complete the Compliance Checklist:")
    
    # The EU AI Act Checklist (Art. 10, 13, 14)
    check_1 = input("[ ] Art 10: Is data quality maintained? (y/n): ")
    check_2 = input("[ ] Art 13: Is the change transparent to users? (y/n): ")
    check_3 = input("[ ] Art 14: Are you assuming full liability? (y/n): ")
    
    if not all(c.lower() == 'y' for c in [check_1, check_2, check_3]):
        print("❌ ACCESS DENIED: Compliance Checklist incomplete. Operation aborted.")
        sys.exit(1)

    justification = input("\nPROMPT: Provide technical justification for the Audit Trail: ")
    
    if len(justification) < 15:
        print("❌ REJECTED: Justification too vague. Minimum 15 characters required.")
        sys.exit(1)

    print("[SYSTEM] Logging to DynamoDB & Triggering AI-Healing Pipeline...")
    
    # 1. Log to Cloud (Traceability)
    warden.table.put_item(Item={
        'IncidentID': f"COMPLIANCE_{warden.datetime.utcnow().timestamp()}",
        'Timestamp': warden.datetime.utcnow().isoformat(),
        'Justification': justification,
        'ComplianceCheck': "ART_10_13_14_PASSED",
        'VerificationHash': warden.generate_verification_hash(diff)
    })

    # 2. AI-Healing (Phase 4 Innovation)
    if ai_heal_documentation(warden, justification, diff):
        print("✅ MISSION COMPLETE: design.md has been self-healed via Nova Lite.")
    else:
        print("⚠️  Warning: Cloud log saved but local documentation sync failed.")

if __name__ == "__main__":
    run_gate()
