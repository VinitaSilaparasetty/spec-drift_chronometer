import json
import asyncio
import datetime
from pathlib import Path
from backend.src.utils.ledger_client import IntentLedgerClient

# Initialize the Sovereign Client
ledger = IntentLedgerClient()

async def log_compliance_event(function_name: str, event_data: dict, justification: str = "Automated System Event"):
    """
    Hybrid Compliance Logger (EU AI Act Article 12)
    Writes to local JSONL for redundancy and pushes to Sovereign Ledger in eu-central-1.
    """
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "function": function_name,
        "data": event_data,
        "justification": justification,
        "compliance_status": "AUDITED"
    }
    
    # 1. Local Redundancy (The "Black Box")
    log_path = Path("logs/intent_ledger.jsonl")
    log_path.parent.mkdir(exist_ok=True)
    
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    # 2. Sovereign Cloud Sync (Phase 4 Active)
    try:
        # We map the event to our DynamoDB Schema
        await ledger.log_intent(
            record_type="SYSTEM_EVENT",
            description=f"Log from {function_name}",
            justification=justification,
            payload=event_data,
            status="AUDITED"
        )
    except Exception as e:
        # Fallback if AWS is unreachable: Log the failure locally
        with open(log_path, "a") as f:
            error_log = {"error": "Cloud Sync Failed", "msg": str(e), "time": timestamp}
            f.write(json.dumps(error_log) + "\n")

if __name__ == "__main__":
    print("Sovereign Hybrid Logger initialized and Region-Locked to eu-central-1.")
