"""
LangChain callback handler that enforces Spec-Drift Chronometer governance.

Wire this into any LangChain chain or agent to enforce EU AI Act Article 14
human oversight. When the Warden detects spec drift above the sovereign threshold,
this handler blocks execution and directs operators to the governance dashboard.

Usage:
    from warden_client import WardenClient
    from warden_callback import WardenCallbackHandler

    warden = WardenClient(base_url="https://your-warden-api.example.com")
    handler = WardenCallbackHandler(warden)

    chain = your_chain.with_config(callbacks=[handler])
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from warden_client import WardenClient, DriftStatus

logger = logging.getLogger("warden")


class WardenGateBlockedException(RuntimeError):
    """
    Raised when the Warden Justification Gate blocks chain execution.

    The chain operator must open the Spec-Drift Chronometer dashboard,
    review the drift, and submit a justification before execution resumes.
    """

    def __init__(self, status: DriftStatus, dashboard_url: str = "http://localhost:3000"):
        self.status = status
        self.dashboard_url = dashboard_url
        super().__init__(
            f"\n"
            f"╔══════════════════════════════════════════════════════════╗\n"
            f"║  WARDEN GATE BLOCKED — Execution halted (Article 14)    ║\n"
            f"╚══════════════════════════════════════════════════════════╝\n"
            f"  Drift index : {status.drift:.4f}\n"
            f"  Threshold   : {status.threshold}\n"
            f"  Gate status : {status.gate}\n"
            f"\n"
            f"  Action required: open the governance dashboard and submit\n"
            f"  a justification to the Warden Agent before retrying.\n"
            f"\n"
            f"  Dashboard → {dashboard_url}\n"
        )


class WardenCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback that checks Spec-Drift Chronometer governance state
    before each chain execution and logs completion to the audit trail.

    Args:
        client: WardenClient connected to your Warden Engine instance.
        dashboard_url: URL shown in the gate-blocked error message.
        raise_on_gate: If True (default), block execution by raising an
            exception. Set False to log a warning and continue — only
            appropriate for read-only or non-critical chains.
        skip_on_warden_unavailable: If True (default), allow execution to
            proceed when the Warden API is unreachable. Set False for strict
            mode where connectivity loss itself halts execution.
    """

    def __init__(
        self,
        client: WardenClient,
        dashboard_url: str = "http://localhost:3000",
        raise_on_gate: bool = True,
        skip_on_warden_unavailable: bool = True,
    ):
        super().__init__()
        self.client = client
        self.dashboard_url = dashboard_url
        self.raise_on_gate = raise_on_gate
        self.skip_on_warden_unavailable = skip_on_warden_unavailable
        self._last_drift: Optional[DriftStatus] = None

    # ------------------------------------------------------------------
    # Core governance hook — fires before every chain run
    # ------------------------------------------------------------------

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        chain_name = (serialized or {}).get("name", "chain")
        try:
            status = self.client.get_drift()
            self._last_drift = status
            logger.info(
                "[Warden] %s | drift=%.4f | gate=%s | status=%s",
                chain_name,
                status.drift,
                status.gate,
                status.status,
            )

            if status.gate in ("TRIGGERED", "PENDING"):
                exc = WardenGateBlockedException(status, self.dashboard_url)
                if self.raise_on_gate:
                    raise exc
                else:
                    logger.warning(str(exc))

        except WardenGateBlockedException:
            raise
        except Exception as exc:
            msg = f"[Warden] Could not reach Warden API: {exc}"
            if self.skip_on_warden_unavailable:
                logger.warning("%s — proceeding without governance check.", msg)
            else:
                raise RuntimeError(msg) from exc

    # ------------------------------------------------------------------
    # Completion logging — fires after every successful chain run
    # ------------------------------------------------------------------

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        if self._last_drift:
            logger.info(
                "[Warden] Chain completed — drift=%.4f | gate=%s",
                self._last_drift.drift,
                self._last_drift.gate,
            )

    # ------------------------------------------------------------------
    # Error logging
    # ------------------------------------------------------------------

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        if isinstance(error, WardenGateBlockedException):
            return
        logger.error("[Warden] Chain error — %s", error)

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        pass

    def on_llm_error(
        self, error: BaseException, *, run_id: UUID, **kwargs: Any
    ) -> None:
        logger.error("[Warden] LLM error — %s", error)
