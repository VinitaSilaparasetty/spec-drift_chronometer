"""
(c) 2026 Aevoxis - Spec-Drift Chronometer
Swarm Registry: Manages the 'Builder' and 'Warden' A2A Negotiation Loop.
"""

from strands import Swarm, Agent
from src.core.warden_brain import WardenSwarm
import json
import datetime

class SwarmRegistry:
    def __init__(self):
        # Initialize the Sovereign Logic Brain
        self.warden_logic = WardenSwarm()
        
        # 1. Define the Builder (The Worker Agent)
        self.builder = Agent(
            role="Builder",
            goal="Generate high-quality Python/AWS code based on user requirements.",
            instructions="You must submit all code changes to the Warden for audit before finalization."
        )
        
        # 2. Define the Warden (The Governance Agent)
        self.warden = Agent(
            role="Warden",
            goal="Enforce EARS requirements and prevent architectural drift in eu-central-1.",
            instructions="Intercept proposals and compare them against the Intent Ledger in DynamoDB."
        )

        # 3. Initialize the Strands Swarm
        self.swarm = Swarm(agents=[self.builder, self.warden])

    def trigger_negotiation(self, proposed_code):
        """
        Executes the 'A2A' (Agent-to-Agent) Negotiation Loop.
        Fulfills EU AI Act requirements for automated traceability.
        """
        print(f"\n[SWARM] Builder proposing change to Sovereign Environment...")
        
        # Ingest the Laws of the Repository
        laws, _ = self.warden_logic.ingest_laws()
        
        # Warden Audit (The Courtroom)
        audit_result = self.warden_logic.perform_audit(laws, proposed_code)
        audit_data = json.loads(audit_result)
        
        # Log the result to the Sovereign Ledger (Frankfurt Region)
        self.warden_logic.table.put_item(
            Item={
                'IncidentID': f"AUDIT-{audit_data.get('status', 'UNKNOWN')}-{int(datetime.datetime.now().timestamp())}",
                'Timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
                'Type': 'A2A_NEGOTIATION',
                'ReasoningTrace': audit_result,
                'ComplianceStatus': audit_data.get('status', 'PENDING'),
                'Region': 'eu-central-1'
            }
        )
        
        return audit_result

if __name__ == "__main__":
    registry = SwarmRegistry()
    print("--- SWARM INITIALIZED: BUILDER & WARDEN READY (eu-central-1) ---")
