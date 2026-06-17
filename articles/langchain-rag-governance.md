# How to Wire EU AI Act Compliance Into a Production LangChain RAG Chatbot

*Published by Vinita Silaparasetty, AI Governance Engineer, Aevoxis Solutions*

---

**Meta description:** Step-by-step guide to connecting EU AI Act Article 14 human oversight into a production LangChain RAG chatbot using the Spec-Drift Chronometer — a real integration pattern for enterprise AI governance teams.

**Target keywords:** EU AI Act compliance LangChain, LangChain human oversight, RAG chatbot governance, Article 14 AI compliance, AI governance integration, LangChain callback EU AI Act, enterprise AI governance Python

---

## The Gap Nobody Talks About

Enterprise teams building AI systems in 2025 have two parallel conversations happening in the same company and almost never in the same room.

The compliance team is mapping obligations from EU AI Act Articles 12, 13, 14 and 50. They are producing gap analyses, risk registers, and conformity frameworks. They know exactly what human oversight must look like on paper.

The engineering team is running a LangChain RAG chatbot in production. It handles customer queries, internal knowledge retrieval, or document summarisation at scale. It is the AI system that the regulation actually applies to.

The gap is that nobody has documented how to connect the governance framework to the running system. The compliance artefacts describe what must happen. The chatbot is what is happening. Between those two things is usually a process document, a ticketing workflow, and a lot of trust.

This article closes that gap with a working integration.

---

## What EU AI Act Article 14 Actually Requires

Article 14 of the EU AI Act mandates human oversight over high-risk AI systems. Specifically, it requires that humans be able to:

- Monitor the AI system's operation in real time
- Understand the system's outputs and their significance
- Override, interrupt, or halt the system when necessary
- Detect and address failures, including unexpected behaviour

The key phrase is *implemented into the AI system by the provider*. This is not a governance document requirement. It is an engineering requirement. The oversight mechanism must be built into how the system executes, not bolted on afterwards via process.

For a LangChain RAG chatbot, this means the human oversight gate must live inside the chain execution path, not in a spreadsheet that someone reviews monthly.

---

## The Architecture: Warden as Governance Sidecar

The Spec-Drift Chronometer (open source, [GitHub](https://github.com/VinitaSilaparasetty/spec-drift_chronometer), [live demo](https://spec-drift-chronometer.aevoxis.de)) implements this as a governance sidecar. The chatbot does not check its own compliance — instead it consults an independent Warden Engine on every execution.

Here is how the data flows:

```
User query
    │
    ▼
LangChain RAG chain
    │
    ├── WardenCallbackHandler fires before execution
    │         │
    │         ▼
    │     GET /drift → Warden Engine returns drift index + gate status
    │         │
    │         ├── gate = CLEAR    → execution proceeds
    │         └── gate = TRIGGERED → execution blocked (Article 14)
    │                               operator must open dashboard, submit
    │                               justification, receive Warden approval
    ▼
Retrieval → Generation → Response
```

The Warden Engine monitors the divergence between the production codebase and the human-authored specification files stored in `.kiro/steering/`. When a developer changes the chatbot's system prompt, swaps out the embedding model, or modifies retrieval parameters without governance sign-off, the drift index rises. When it crosses the sovereign threshold, the gate triggers and every subsequent chain execution is blocked until a human completes the justification workflow.

This is Article 14 implemented in code, not documented in a process.

---

## What Causes Drift in a RAG Chatbot?

Before showing the integration, it helps to understand what the Warden is actually measuring.

The drift score is the fraction of meaningful tokens in the latest code change that are absent from the vocabulary of the human-authored spec files. A change that introduces new architectural concepts not covered by the approved spec scores higher. A refactor that uses only terms already present in the spec scores lower.

For a LangChain RAG chatbot, the changes that produce high drift are:

**High-drift changes** (typically require human sign-off):
- Changing the system prompt to give the AI a different persona or scope
- Switching to a more capable or different family of model
- Modifying the retrieval strategy (chunk size, overlap, top-k, similarity threshold)
- Adding tool use or agent capabilities not in the original specification
- Changing the data sources indexed in the vector store

**Low-drift changes** (typically within sovereign bounds):
- Dependency version bumps that do not change API surface
- Logging and observability additions
- Fixing a spelling error in a document
- Performance optimisations using the same approved approach

The Warden does not require you to enumerate these categories manually. It reads your spec files, reads the git diff, and computes the divergence. The human-authored specs in `.kiro/steering/` are the source of truth.

---

## The Integration: Three Files

### Step 1: Install dependencies

```bash
cd integrations/langchain_rag
pip install -r requirements.txt
```

The dependencies are `langchain-core`, `langchain-community`, `faiss-cpu`, and `requests`. No new AI frameworks are required.

### Step 2: The Warden client

`warden_client.py` is a 50-line HTTP wrapper. It polls the Warden Engine's `/drift` endpoint and returns a typed `DriftStatus` object. It also exposes `submit_justification` for programmatic approval workflows.

```python
from warden_client import WardenClient

warden = WardenClient(base_url="https://your-warden-api.example.com")
status = warden.get_drift()
print(status.drift)   # 0.0082
print(status.gate)    # "TRIGGERED"
```

### Step 3: The callback handler

`warden_callback.py` implements `BaseCallbackHandler`. The one method that matters is `on_chain_start` — it fires before every chain execution and checks the gate.

```python
from langchain_core.callbacks import BaseCallbackHandler

class WardenCallbackHandler(BaseCallbackHandler):
    def on_chain_start(self, serialized, inputs, *, run_id, **kwargs):
        status = self.client.get_drift()
        if status.gate in ("TRIGGERED", "PENDING"):
            raise WardenGateBlockedException(status, self.dashboard_url)
```

The full implementation handles connectivity failures, warning-only mode, and structured error messages that tell the operator exactly what to do.

### Step 4: Wire it into your chain

This is the only change to your existing chatbot:

```python
from warden_client import WardenClient
from warden_callback import WardenCallbackHandler

warden = WardenClient(base_url="https://your-warden-api.example.com")
handler = WardenCallbackHandler(
    client=warden,
    dashboard_url="https://your-dashboard.example.com",
    raise_on_gate=True,
    skip_on_warden_unavailable=True,   # degrade gracefully if Warden is down
)

# Your existing chain — unchanged except for this one line
rag_chain = (your_existing_rag_chain).with_config(callbacks=[handler])
```

The `with_config(callbacks=[handler])` pattern works with any LCEL chain, LangGraph graph, or LangChain agent. The chain itself does not change. The Warden observes it from outside.

---

## What the Operator Sees When the Gate Triggers

When a developer commits an unapproved change and the drift crosses the sovereign threshold, the next API call to the chatbot returns this instead of a generated answer:

```
╔══════════════════════════════════════════════════════════╗
║  WARDEN GATE BLOCKED — Execution halted (Article 14)    ║
╚══════════════════════════════════════════════════════════╝
  Drift index : 0.0091
  Threshold   : 0.0075
  Gate status : TRIGGERED

  Action required: open the governance dashboard and submit
  a justification to the Warden Agent before retrying.

  Dashboard → https://spec-drift-chronometer.aevoxis.de
```

The operator opens the dashboard, sees the drift chart, reads the Warden activity log showing which file changed, and submits a justification explaining the change. The Warden Agent — Amazon Nova Pro in production — evaluates the justification against the spec files and returns an Intent Alignment Score. A substantive justification (for example: "Migrating from GPT-3.5 to GPT-4o-mini — approved by architecture review board 2026-06-10, ticket ARCH-291") scores 91/100 and is APPROVED. A weak one ("updated model") scores 29/100 and is REJECTED.

Once APPROVED, the gate clears. The chatbot resumes accepting queries on the next execution.

Every gate event — justification text, drift value, Warden decision, reasoning trace, SHA-256 verification hash — is written to `.kiro/audit/last_sync.audit` and can be downloaded directly from the dashboard. This is the Article 12 record-keeping artefact.

---

## Running the Full Example

The repository includes a complete working RAG chatbot with FAISS vector store and the Warden integration pre-wired.

```bash
# Clone the repository
git clone https://github.com/VinitaSilaparasetty/spec-drift_chronometer.git
cd spec-drift_chronometer

# Start the Warden Engine (demo mode — no AWS credentials needed)
DEMO_MODE=true ./dev.sh

# In a second terminal: run the example chatbot
cd integrations/langchain_rag
pip install -r requirements.txt
OPENAI_API_KEY=demo python rag_chatbot.py
```

The `OPENAI_API_KEY=demo` flag runs the chatbot with a fake LLM so you can observe the Warden integration without an API key. When the demo scenario advances into `CRITICAL_DRIFT`, the chatbot will block the next query and display the gate message. Open `http://localhost:3000`, submit a justification, and watch the gate clear.

---

## Deployment Considerations

**Warden API availability.** The `skip_on_warden_unavailable=True` default allows the chatbot to continue if the Warden is unreachable. For high-risk systems, set this to `False` to enforce strict mode: any connectivity loss halts execution.

**Latency.** The `/drift` poll adds one HTTP round trip per chain invocation. The Warden API is designed to respond within 200 ms. For high-throughput systems, cache the gate status with a short TTL (5–10 seconds) rather than polling on every call.

**Multi-tenant deployments.** Each project should have its own Warden instance and its own `.kiro/steering/` spec vault. The spec files define what "sovereign" looks like for that specific system, so sharing them across products produces meaningless drift scores.

**DynamoDB audit trail.** In production, set `DYNAMODB_TABLE_NAME` and AWS credentials to persist every gate event to DynamoDB with a configurable retention TTL. This produces a durable, queryable audit trail — useful for regulatory inspections and incident reviews.

---

## The Compliance Argument to Your Legal Team

If your legal team asks what Article 14 evidence you can produce for a conformity assessment, the answer with this integration is:

1. **Gate log.** A timestamped record of every execution that was blocked, the justification submitted, the Warden reasoning trace, and the APPROVED/REJECTED decision.
2. **Audit trail.** A downloadable SHA-256-verified file covering every governance event in the session.
3. **Architecture documentation.** The Warden callback is in the production code path, not a process document. Human oversight is enforced at execution, not at review.
4. **Spec vault.** The human-authored specifications that define what compliant behaviour looks like are version-controlled, timestamped, and referenced in every Warden decision.

This is the difference between documenting compliance and engineering it.

---

## Next Steps

- [Try the live demo](https://spec-drift-chronometer.aevoxis.de) — observe the full governance cycle in real time
- [Read the GitHub repository](https://github.com/VinitaSilaparasetty/spec-drift_chronometer) — integration code is in `integrations/langchain_rag/`
- [AWS Community Builder submission](https://builder.aws.com/content/3ArZsXU7l4aaXPzFdXH0DdlyaM4/aideas-spec-drift-chronometer) — full technical write-up from the AWS 10,000 AIdeas Competition
- For commercial deployment or enterprise licensing: info@aevoxis.de

---

*Vinita Silaparasetty is an AI Governance Engineer at Aevoxis Solutions (aevoxis.de), specialising in EU AI Act compliance architecture for enterprise AI deployments. The Spec-Drift Chronometer is a Top 300 finalist in the AWS 10,000 AIdeas Competition 2025.*
