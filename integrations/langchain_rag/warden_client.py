"""
Thin HTTP client for the Spec-Drift Chronometer Warden API.
Drop this into any Python AI project to gain governance awareness.
"""

from __future__ import annotations
import requests
from dataclasses import dataclass


@dataclass
class DriftStatus:
    drift: float
    status: str
    threshold: float
    gate: str
    demo_mode: bool


class WardenClient:
    """Speaks to the Warden Engine API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_drift(self) -> DriftStatus:
        """Poll current drift index and gate state."""
        r = requests.get(f"{self.base_url}/drift", timeout=self.timeout)
        r.raise_for_status()
        d = r.json()
        return DriftStatus(
            drift=d["drift"],
            status=d["status"],
            threshold=d["threshold"],
            gate=d["gate"],
            demo_mode=d.get("demo_mode", False),
        )

    def get_gate_status(self) -> dict:
        """Return the current gate state and last decision."""
        r = requests.get(f"{self.base_url}/gate/status", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def submit_justification(self, justification: str, drift_value: float) -> dict:
        """
        Submit a human justification to the Warden Agent.
        Returns the Warden's APPROVED/REJECTED decision with reasoning trace.
        """
        r = requests.post(
            f"{self.base_url}/gate/submit",
            json={"justification": justification, "drift_value": drift_value},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
