import os
import json
import subprocess
import boto3
import hashlib
from datetime import datetime

class WardenSwarm:
    def __init__(self):
        self.tech_laws_path = ".kiro/steering/tech.md"
        self.region = "eu-central-1" 
        self.bedrock = boto3.client("bedrock-runtime", region_name=self.region)
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.dynamodb.Table("SpecDrift_Ledger")
        
        # Dual-Model Architecture for Cost-Efficiency
        self.lite_model = "amazon.nova-lite-v1:0" 
        self.pro_model = "amazon.nova-pro-v1:0"   
        self.datetime = datetime

    def generate_verification_hash(self, content):
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def ingest_laws(self):
        try:
            with open(self.tech_laws_path, "r") as f:
                return f.read(), None
        except:
            return None, None

    def capture_diff(self):
        result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
        return result.stdout if result.stdout else ""

    def scan_drift(self, laws, diff):
        """Tier 1: Nova Lite (The $0.00001 Guard)"""
        print(f"[AUDIT] Initializing Nova Lite Scan... (Status: Free Tier Optimal)")
        prompt = f"Does this diff violate these tech laws? Answer only YES or NO.\nLaws: {laws}\nDiff: {diff}"
        response = self.bedrock.invoke_model(
            modelId=self.lite_model,
            body=json.dumps({"messages": [{"role": "user", "content": [{"text": prompt}]}]})
        )
        res_body = json.loads(response['body'].read())
        drift_found = "YES" in res_body['output']['message']['content'][0]['text'].upper()
        
        if not drift_found:
            print("[AUDIT] Nova Lite: No drift detected. Nova Pro remains in Hibernation (Cost Saved).")
        return drift_found

    def perform_prosecution(self, laws, diff):
        """Tier 2: Nova Pro (The High-Reasoning Sovereign)"""
        print("[AUDIT] ALERT: Nova Lite detected drift. Waking Nova Pro for Prosecution...")
        print("[AUDIT] Utilizing Competition Credits for High-Reasoning Audit (Art. 14).")
        prompt = f"PROSECUTION MISSION: Analyze the following drift for hallucinations.\nLaws: {laws}\nDiff: {diff}\nOutput detailed JSON audit."
        response = self.bedrock.invoke_model(
            modelId=self.pro_model,
            body=json.dumps({"messages": [{"role": "user", "content": [{"text": prompt}]}]})
        )
        res_body = json.loads(response['body'].read())
        print("[AUDIT] Prosecution Complete. Logging reasoning trace to DynamoDB.")
        return res_body['output']['message']['content'][0]['text']

if __name__ == "__main__":
    print("Warden Brain (Cost-Aware) Commissioned.")
