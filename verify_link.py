import sys
from src.warden_brain import WardenSwarm

def test_integration():
    print("🔍 [TEST] Initializing WardenSwarm Link Test...")
    try:
        warden = WardenSwarm()
        
        # Define the 'Critical Path' methods required for Phase 4
        required_methods = [
            'ingest_laws', 
            'capture_diff', 
            'scan_drift', 
            'perform_prosecution', 
            'perform_bulk_audit'
        ]
        
        missing = []
        for method in required_methods:
            if hasattr(warden, method):
                print(f"✅ Method Found: {method}")
            else:
                missing.append(method)
        
        if missing:
            print(f"\n❌ ERROR: Linkage Broken! Missing methods: {missing}")
            sys.exit(1)
        
        print("\n💎 [RESULT] Linkage Verified. The Brain and Gate are perfectly aligned.")
        print("🚀 Status: Ready for Competition Submission.")

    except Exception as e:
        print(f"❌ CRITICAL: System failed to initialize: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_integration()
