import os
import json

class WardenBrain:
    def __init__(self):
        self.tech_laws_path = ".kiro/steering/tech.md"
        self.spec_path = ".kiro/steering/spec.json"

    def ingest_laws(self):
        """Reads the steering documents to establish Ground Truth."""
        try:
            with open(self.tech_laws_path, "r") as f:
                tech_laws = f.read()
            
            with open(self.spec_path, "r") as f:
                spec_data = json.load(f)
                
            print("[INFO] Warden Brain: Laws successfully ingested.")
            return tech_laws, spec_data
        except Exception as e:
            print(f"[ERROR] Failed to ingest laws: {e}")
            return None, None

if __name__ == "__main__":
    warden = WardenBrain()
    laws, spec = warden.ingest_laws()
    if laws:
        print("--- Current Tech Law Snippet ---")
        print(laws[:150] + "...") # Print first 150 chars to verify
