import boto3
import datetime
import uuid

class IntentLedgerClient:
    def __init__(self, table_name="SpecDrift_Ledger"):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    async def log_intent(self, project_id, record_type, use_case, payload, justification, approval=True):
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        intent_id = f"{timestamp}#{uuid.uuid4().hex[:8]}"
        
        item = {
            'ProjectID': project_id,
            'IntentID': intent_id,
            'RecordType': record_type,
            'UseCase': use_case,
            'Payload': payload,
            'Justification': justification,
            'Sovereign_Approval': approval,
            'Created_At': timestamp
        }
        self.table.put_item(Item=item)
        return intent_id
