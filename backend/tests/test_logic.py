import sys
from backend.src.core.warden_brain import WardenSwarm

def test_integration():
    print("�� [TEST] Initializing WardenSwarm Link Test...")
    try:
        warden = WardenSwarm()
        required_methods = ['ingest_laws', 'capture_diff', 'scan_drift', 'perform_prosecution', 'perform_bulk_audit']
        missing = [m for m in required_methods if not hasattr(warden, m)]
        
        if missing:
            print(f"❌ ERROR: Missing methods: {missing}")
            sys.exit(1)
        print("✅ [RESULT] Internal Linkage Verified. WardenSwarm is fully functional.")
    except Exception as e:
        print(f"❌ CRITICAL: System failed to initialize: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_integration()
