import sys
import json
from backend.src.core.warden_brain import WardenSwarm

def main():
    print("--- Spec-Drift Chronometer: Sovereign Initialization ---")

    # 1. Environment Verification (German Standard: Determinism)
    if sys.version_info[:2] != (3, 12):
        print(f"CRITICAL ERROR: Environment mismatch. Expected 3.12, found {sys.version_info[0]}.{sys.version_info[1]}")
        sys.exit(1)

    # 2. Governance Loading
    try:
        with open(".kiro/config.json", "r") as f:
            config = json.load(f)
        region = config.get("governance", {}).get("sovereign_region", "unknown")
        print(f"STATUS: Governance Loaded. Target Region: {region}")
    except FileNotFoundError:
        print("CRITICAL ERROR: .kiro/config.json not found. System non-compliant.")
        sys.exit(1)

    # 3. Awakening the Warden Swarm
    try:
        print("STATUS: Awakening Warden Swarm...")
        # We use the updated class name here
        warden = WardenSwarm()
        print("SUCCESS: System is active and monitoring for Spec-Drift.")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize Warden Swarm: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
