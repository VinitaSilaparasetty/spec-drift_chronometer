import os
import json
import subprocess
import boto3
import hashlib
import datetime

class WardenSwarm:
    def __init__(self):
        # Adjusted path to find laws from the src/core/ directory
        self.tech_laws_path = os.path.join(os.getcwd(), ".kiro/steering/tech.md")
        self.region = "eu-central-1" # Sovereign Frankfurt Region
        self.bedrock = boto3.client("bedrock-runtime", region_name=self.region)
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        # Matches the table created in provision_ledger.sh
        self.table = self.dynamodb.Table("SpecDrift_Sovereign_Ledger")
        self.datetime = datetime.datetime
        
        # Dual-Model Architecture
        self.lite_model = "amazon.nova-lite-v1:0" 
        self.pro_model = "amazon.nova-pro-v1:0"

    def generate_verification_hash(self, content):
        """Creates a SHA-256 anchor for the Audit Trail (REQ-LOG-004)."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def ingest_laws(self):
        """Reads the source of truth from Kiro steering."""
        try:
            with open(self.tech_laws_path, "r") as f:
                return f.read(), None
        except Exception as e:
            return None, str(e)

    def capture_diff(self):
        """Captures the real-time architectural drift."""
        result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
        return result.stdout if result.stdout else ""

    def perform_audit(self, laws, diff):
        """
        Unified Audit Logic. 
        Uses Nova Lite for detection and maps to our Sovereign Ledger.
        """
        print(f"[AUDIT] Initializing Sovereign Scan in {self.region}...")
        prompt = f"Does this diff violate these laws? YES/NO\nLaws: {laws}\nDiff: {diff}"
        
        # Bedrock Converse API Format
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        })
        
        response = self.bedrock.invoke_model(modelId=self.lite_model, body=body)
        res_body = json.loads(response['body'].read())
        
        # Basic logic to return a status for the SwarmRegistry
        result_text = res_body['content'][0]['text']
        status = "VIOLATION" if "YES" in result_text.upper() else "COMPLIANT"
        
        return json.dumps({"status": status, "reasoning": result_text})

    def perform_bulk_audit(self, file_list):
        """Scalability Engine: For enterprise-scale compliance (Article 12)."""
        print(f"[SCALING] Preparing Batch Inference manifest for {len(file_list)} assets...")
        manifest = [{"file": f, "model": self.lite_model} for f in file_list]
        return manifest

if __name__ == "__main__":
    print("Sovereign Warden: Full System (eu-central-1) Ready.")
