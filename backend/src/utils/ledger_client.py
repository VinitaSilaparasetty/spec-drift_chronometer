import boto3
import datetime
import uuid
import hashlib
import json
from botocore.config import Config

class IntentLedgerClient:
    """
    Sovereign Intent Ledger Client
    Enforces compliance with German regional constraints (eu-central-1).
    """
    def __init__(self, table_name="SpecDrift_Sovereign_Ledger"):
        # Explicitly locking to Frankfurt region for German regulatory compliance
        my_config = Config(region_name='eu-central-1')
        self.dynamodb = boto3.resource('dynamodb', config=my_config)
        self.table = self.dynamodb.Table(table_name)

    def _generate_verification_hash(self, payload):
        """REQ-LOG-004: Generate SHA-256 hash for immutable audit trail."""
        dump = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(dump.encode()).hexdigest()

    async def log_intent(self, record_type, description, justification, payload=None, status="APPROVED"):
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        # IncidentID is our HASH key; Timestamp is our RANGE key
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        
        verification_hash = self._generate_verification_hash(payload or {})

        item = {
            'IncidentID': incident_id,
            'Timestamp': timestamp,
            'Type': record_type,
            'ComplianceStatus': status, # Matches GSI for quick auditing
            'Description': description,
            'Justification': justification,
            'Payload': payload or {},
            'VerificationHash': f"sha256:{verification_hash}",
            'Region': 'eu-central-1'
        }
        
        # Article 12/14 Traceability: Logging the write action
        self.table.put_item(Item=item)
        return incident_id
