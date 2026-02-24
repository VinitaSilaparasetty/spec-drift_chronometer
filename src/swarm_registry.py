from strands import Swarm, Agent
from src.warden_brain import WardenSwarm
import json

class SwarmRegistry:
    def __init__(self):
        self.warden_logic = WardenSwarm()
        
        # 1. Define the Builder (The Worker)
        self.builder = Agent(
            role="Builder",
            goal="Generate high-quality Python/AWS code based on user requirements.",
            instructions="You must submit all code changes to the Warden for audit before finalization."
        )
        
        # 2. Define the Warden (The Judge)
        self.warden = Agent(
            role="Warden",
            goal="Enforce EARS requirements and prevent architectural drift.",
            instructions="You intercept Builder proposals and compare them against the Intent Ledger in DynamoDB."
        )

        # 3. Initialize the Strands Swarm
        self.swarm = Swarm(agents=[self.builder, self.warden])

    def trigger_negotiation(self, proposed_code):
        """
        Executes the 'A2A' Negotiation Loop (Phase 3).
        The Builder proposes -> The Warden Intercepts.
        """
        print(f"\n[SWARM] Builder proposing change...")
        
        # Get Laws and Diff for the Warden
        laws, _ = self.warden_logic.ingest_laws()
        
        # Warden Audit (The Courtroom)
        audit_result = self.warden_logic.perform_audit(laws, proposed_code)
        
        # Log the result to the Ledger (Phase 2 Requirement)
        self.warden_logic.table.put_item(
            Item={
                'IncidentID': f"AUDIT_{json.loads(audit_result).get('status', 'UNKNOWN')}",
                'Timestamp': self.warden_logic.datetime.utcnow().isoformat(),
                'Type': 'A2A_NEGOTIATION',
                'ReasoningTrace': audit_result,
                'Status': 'LOGGED'
            }
        )
        
        return audit_result

if __name__ == "__main__":
    registry = SwarmRegistry()
    print("--- SWARM INITIALIZED: BUILDER & WARDEN READY ---")
