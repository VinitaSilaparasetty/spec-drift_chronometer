import sys
from src.warden_brain import WardenSwarm

def run_gate():
    warden = WardenSwarm()
    laws, _ = warden.ingest_laws()
    diff = warden.capture_diff()
    
    # Check if there's actual drift
    if "No changes detected" in diff or not diff:
        return

    print("\n⚠️  WARDEN DETECTED ARCHITECTURAL DRIFT")
    print("----------------------------------------")
    justification = input("PROMPT: Please provide technical justification for this deviation: ")
    
    if len(justification) < 10:
        print("❌ REJECTED: Justification too brief. Try again.")
        sys.exit(1)

    # Self-Healing: Update design.md
    with open("design.md", "a") as f:
        f.write(f"\n## Approved Drift - {warden.datetime.utcnow().isoformat()}\n")
        f.write(f"Justification: {justification}\n")
        f.write(f"Hash: {warden.generate_verification_hash(diff)[:12]}\n")
    
    print("✅ JUSTIFICATION LOGGED. Self-healing design.md sync complete.")

if __name__ == "__main__":
    run_gate()
