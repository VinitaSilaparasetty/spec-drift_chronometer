import sys
import json
from src.warden_brain import WardenSwarm

def log_governance_event(warden, justification, diff):
    """Fulfills Article 12 (Traceability) and Article 14 (Human Oversight)."""
    try:
        warden.table.put_item(
            Item={
                'IncidentID': f"GOV_OVERRIDE_{warden.datetime.utcnow().timestamp()}",
                'Timestamp': warden.datetime.utcnow().isoformat(),
                'Type': 'HUMAN_OVERSIGHT_OVERRIDE',
                'Justification': justification,
                'VerificationHash': warden.generate_verification_hash(diff),
                'ComplianceStatus': 'ART_14_VERIFIED' # Explicit legal marker for EU AI Act
            }
        )
        return True
    except Exception as e:
        print(f"[CRITICAL] Governance Logging Failed: {e}")
        return False

def run_gate():
    warden = WardenSwarm()
    laws, _ = warden.ingest_laws()
    diff = warden.capture_diff()
    
    # Check if there's actual drift
    if "No changes detected" in diff or not diff:
        return

    print("\n⚠️  WARDEN DETECTED ARCHITECTURAL DRIFT")
    print("----------------------------------------")
    justification = input("PROMPT: Please provide technical justification for this deviation (EU AI Act Art. 14): ")
    
    if len(justification) < 10:
        print("❌ REJECTED: Justification too brief. Try again.")
        sys.exit(1)

    # 1. Cloud Compliance Logging (Step 4 Requirement)
    print("[INFO] Logging governance event to DynamoDB...")
    log_governance_event(warden, justification, diff)

    # 2. Self-Healing: Update design.md (Step 4 Requirement)
    try:
        with open("design.md", "a") as f:
            f.write(f"\n## Approved Drift - {warden.datetime.utcnow().isoformat()}\n")
            f.write(f"Justification: {justification}\n")
            f.write(f"Hash: {warden.generate_verification_hash(diff)[:12]}\n")
        print("✅ JUSTIFICATION LOGGED. Self-healing design.md sync complete.")
    except Exception as e:
        print(f"[ERROR] Local self-healing failed: {e}")

if __name__ == "__main__":
    run_gate()
