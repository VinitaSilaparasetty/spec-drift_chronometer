import os
import json
import subprocess

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
            return tech_laws, spec_data
        except Exception as e:
            print(f"[ERROR] Ingestion failed: {e}")
            return None, None

    def capture_diff(self):
        """The 'Observer' logic: Captures uncommitted changes (the #Git Diff)."""
        try:
            # Captures both staged and unstaged changes
            result = subprocess.run(
                ["git", "diff", "HEAD"], 
                capture_output=True, text=True
            )
            diff_text = result.stdout
            if not diff_text:
                return "No changes detected in the workspace."
            return diff_text
        except Exception as e:
            return f"[ERROR] Could not capture Git Diff: {e}"

if __name__ == "__main__":
    warden = WardenBrain()
    laws, spec = warden.ingest_laws()
    current_diff = warden.capture_diff()
    
    print("--- WARDEN BRAIN: STATE CAPTURE ---")
    if laws: print("[PASS] Laws Loaded.")
    if current_diff: 
        print(f"[INFO] Diff Captured ({len(current_diff)} characters).")
        print("\n--- LIVE GIT DIFF SNIPPET ---")
        print(current_diff[:200] + "...")
