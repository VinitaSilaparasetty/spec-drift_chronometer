"""
Enterprise RAG chatbot with Spec-Drift Chronometer governance.

Demonstrates how to wire the Warden Engine into a production LangChain
RAG pipeline so that EU AI Act Article 14 human oversight is enforced
before every chain execution.

Requirements:
    pip install -r requirements.txt

Environment variables:
    WARDEN_API_URL   — URL of the Warden Engine (default: http://localhost:8000)
    WARDEN_DASH_URL  — URL of the governance dashboard (default: http://localhost:3000)
    OPENAI_API_KEY   — Required for live embeddings and generation
                       Set to "demo" to run with fake models (no API key needed)

Quick start (demo mode, no API keys):
    OPENAI_API_KEY=demo python rag_chatbot.py

With live Warden + OpenAI:
    WARDEN_API_URL=https://your-warden.example.com \\
    OPENAI_API_KEY=sk-... \\
    python rag_chatbot.py
"""

from __future__ import annotations
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WARDEN_API_URL = os.environ.get("WARDEN_API_URL", "http://localhost:8000")
WARDEN_DASH_URL = os.environ.get("WARDEN_DASH_URL", "http://localhost:3000")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEMO_LLM = not OPENAI_API_KEY or OPENAI_API_KEY == "demo"

# ---------------------------------------------------------------------------
# Sample knowledge base — replace with your document loader
# ---------------------------------------------------------------------------

SAMPLE_DOCS = [
    "Our refund policy allows returns within 30 days of purchase with a valid receipt.",
    "Premium members receive free shipping on all orders over €50.",
    "Customer support is available Monday to Friday, 09:00–18:00 CET.",
    "All personal data is processed in EU data centres in compliance with GDPR.",
    "Product warranties are valid for 24 months from the date of purchase.",
    "Our AI systems are governed under EU AI Act compliance framework version 2025.",
]

# ---------------------------------------------------------------------------
# Warden governance setup (the integration)
# ---------------------------------------------------------------------------

from warden_client import WardenClient
from warden_callback import WardenCallbackHandler, WardenGateBlockedException

warden = WardenClient(base_url=WARDEN_API_URL)
warden_handler = WardenCallbackHandler(
    client=warden,
    dashboard_url=WARDEN_DASH_URL,
    raise_on_gate=True,           # block execution if gate triggers
    skip_on_warden_unavailable=True,  # degrade gracefully if Warden is down
)

# ---------------------------------------------------------------------------
# Embeddings and vector store
# ---------------------------------------------------------------------------

from langchain_core.documents import Document

if DEMO_LLM:
    from langchain_community.embeddings import FakeEmbeddings
    from langchain_core.language_models import FakeListLLM

    embeddings = FakeEmbeddings(size=384)
    llm = FakeListLLM(
        responses=[
            "Based on our policy, refunds are available within 30 days of purchase.",
            "Premium members enjoy free shipping on orders over €50.",
            "Customer support operates Monday–Friday, 09:00–18:00 CET.",
        ]
    )
    print("[Demo] Running with fake LLM and embeddings — no API key required.")
    print(f"[Demo] To use real OpenAI models, set OPENAI_API_KEY in your environment.\n")
else:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI

    embeddings = OpenAIEmbeddings()
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    print(f"[Live] Using OpenAI models.\n")

from langchain_community.vectorstores import FAISS

docs = [Document(page_content=text) for text in SAMPLE_DOCS]
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ---------------------------------------------------------------------------
# RAG chain assembly
# ---------------------------------------------------------------------------

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful enterprise assistant. Answer the user's question "
        "using only the provided context. If the answer is not in the context, "
        "say so. Be concise and accurate.\n\nContext:\n{context}",
    ),
    ("human", "{question}"),
])


def format_docs(docs: list) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


# The RAG chain — Warden callback is attached here
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
).with_config(
    # ← This single line wires in EU AI Act Article 14 governance
    callbacks=[warden_handler]
)

# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

EXAMPLE_QUESTIONS = [
    "What is the refund policy?",
    "Do premium members get free shipping?",
    "When is customer support available?",
]


def run_query(question: str) -> str:
    """Run a single RAG query through the governance-aware chain."""
    try:
        return rag_chain.invoke(question)
    except WardenGateBlockedException as exc:
        # Surface the Warden message to the end user / operator
        return str(exc)
    except Exception as exc:
        return f"Error: {exc}"


def main() -> None:
    print("=" * 62)
    print("  Enterprise RAG Chatbot — Governed by Spec-Drift Chronometer")
    print("=" * 62)
    print(f"  Warden API  : {WARDEN_API_URL}")
    print(f"  Dashboard   : {WARDEN_DASH_URL}")
    print()

    # Check Warden connectivity on startup
    try:
        status = warden.get_drift()
        print(f"  Warden status : {status.status} | drift={status.drift:.4f} | gate={status.gate}")
    except Exception as exc:
        print(f"  Warden status : UNREACHABLE ({exc})")
        print("  Proceeding in degraded mode — no governance checks will run.\n")
    print()

    if len(sys.argv) > 1:
        # Single question from CLI argument
        question = " ".join(sys.argv[1:])
        print(f"Q: {question}")
        print(f"A: {run_query(question)}\n")
        return

    # Run example questions
    for question in EXAMPLE_QUESTIONS:
        print(f"Q: {question}")
        answer = run_query(question)
        print(f"A: {answer}\n")

    # Interactive mode
    print("─" * 62)
    print("Type a question (or 'quit' to exit):")
    while True:
        try:
            question = input("\nQ: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue
        print(f"A: {run_query(question)}")


if __name__ == "__main__":
    main()
