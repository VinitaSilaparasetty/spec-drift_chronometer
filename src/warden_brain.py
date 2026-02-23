import os
import json
import subprocess
import boto3
import hashlib
from datetime import datetime

class WardenSwarm:
    def __init__(self):
        self.tech_laws_path = ".kiro/steering/tech.md"
        self.spec_path = ".kiro/steering/spec.json"
        self.region = "eu-central-1" # Sovereign Frankfurt Region
        
        # AWS Clients
        self.bedrock = boto3.client("bedrock-runtime", region_name=self.region)
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.dynamodb.Table("SpecDrift_Ledger")
        self.model_id = "amazon.nova-pro-v1:0"

    def generate_verification_hash(self, content):
        """Generates a SHA-256 hash to create an Immutable Audit Trail."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

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

    def sync_spec_to_cloud(self, tech_laws):
        """Uploads EARS laws + Verification Hash to DynamoDB."""
        try:
            v_hash = self.generate_verification_hash(tech_laws)
            self.table.put_item(
                Item={
                    'IncidentID': 'ACTIVE_SPEC_LATEST',
                    'Timestamp': datetime.utcnow().isoformat(),
                    'Type': 'SYSTEM_GOVERNANCE',
                    'VerificationHash': v_hash,
                    'RawMarkdown': tech_laws,
                    'Status': 'ACTIVE'
                }
            )
            print(f"[INFO] Verification Hash Generated: {v_hash[:12]}...")
            return True
        except Exception as e:
            print(f"[ERROR] Spec sync failed: {e}")
            return False

    def capture_diff(self):
        """Captures uncommitted changes."""
        try:
            result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
            return result.stdout if result.stdout else "No changes detected."
        except Exception as e:
            return f"[ERROR] Could not capture Git Diff: {e}"

    def perform_audit(self, laws, diff):
        """Nova Pro Reasoning Task."""
        if not laws or not diff or "No changes detected" in diff:
            return {"status": "SKIPPED", "reasoning": "No input for audit."}

        prompt = f"AUDIT MISSION: Compare Diff against Tech Laws.\n\nLAWS:\n{laws}\n\nDIFF:\n{diff}\n\nOutput JSON."
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "inferenceConfig": {"max_new_tokens": 1000, "temperature": 0},
                    "messages": [{"role": "user", "content": [{"text": prompt}]}]
                })
            )
            response_body = json.loads(response['body'].read())
            return response_body['output']['message']['content'][0]['text']
        except Exception as e:
            return {"status": "ERROR", "reasoning": str(e)}

if __name__ == "__main__":
    warden = WardenSwarm()
    laws, spec = warden.ingest_laws()
    if laws:
        warden.sync_spec_to_cloud(laws)
    
    current_diff = warden.capture_diff()
    print(warden.perform_audit(laws, current_diff))
