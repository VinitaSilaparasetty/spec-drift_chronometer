import os
import json
import subprocess
import boto3

class WardenSwarm:
    def __init__(self):
        # Retained from WardenBrain
        self.tech_laws_path = ".kiro/steering/tech.md"
        self.spec_path = ".kiro/steering/spec.json"
        
        # Added for Agentic Core (Sovereign Frankfurt Region)
        self.bedrock = boto3.client("bedrock-runtime", region_name="eu-central-1")
        self.model_id = "amazon.nova-pro-v1:0"

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

    def perform_audit(self, laws, diff):
        """The Nova Pro Reasoning Task: Drift vs. Hallucination."""
        if not laws or not diff or "No changes detected" in diff:
            return {"status": "SKIPPED", "reasoning": "No input for audit."}

        prompt = f"AUDIT MISSION: Compare Diff against Tech Laws.\n\nLAWS:\n{laws}\n\nDIFF:\n{diff}\n\nOutput JSON with status, reasoning, and recommended_action."
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "inferenceConfig": {"max_new_tokens": 1000, "temperature": 0},
                    "messages": [{"role": "user", "content": [{"text": prompt}]}]
                })
            )
            # Nova response parsing
            response_body = json.loads(response['body'].read())
            return response_body['output']['message']['content'][0]['text']
        except Exception as e:
            return {"status": "ERROR", "reasoning": str(e)}

if __name__ == "__main__":
    warden = WardenSwarm()
    laws, spec = warden.ingest_laws()
    current_diff = warden.capture_diff()
    
    print("--- WARDEN BRAIN: STATE CAPTURE ---")
    if laws: print("[PASS] Laws Loaded.")
    if current_diff: 
        print(f"[INFO] Diff Captured ({len(current_diff)} characters).")
        
    print("\n--- INITIATING NOVA PRO AUDIT ---")
    verdict = warden.perform_audit(laws, current_diff)
    print(verdict)
