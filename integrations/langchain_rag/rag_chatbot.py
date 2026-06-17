"""
Enterprise RAG chatbot with Spec-Drift Chronometer governance.

Demonstrates how to wire the Warden Engine into a production LangChain
RAG pipeline so that EU AI Act Article 14 human oversight is enforced
before every chain execution.

Setup:
    cp .env.example .env
    # Fill in OPENAI_API_KEY in .env
    pip install -r requirements.txt
    python rag_chatbot.py
"""

from __future__ import annotations
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")

WARDEN_API_URL = os.environ.get("WARDEN_API_URL", "http://localhost:8000")
WARDEN_DASH_URL = os.environ.get("WARDEN_DASH_URL", "http://localhost:3000")

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
# Warden governance setup
# ---------------------------------------------------------------------------

from warden_client import WardenClient
from warden_callback import WardenCallbackHandler, WardenGateBlockedException

warden = WardenClient(base_url=WARDEN_API_URL)
warden_handler = WardenCallbackHandler(
    client=warden,
    dashboard_url=WARDEN_DASH_URL,
    raise_on_gate=True,
    skip_on_warden_unavailable=True,
)

# ---------------------------------------------------------------------------
# Embeddings, vector store, and LLM
# ---------------------------------------------------------------------------

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

docs = [Document(page_content=text) for text in SAMPLE_DOCS]
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ---------------------------------------------------------------------------
# RAG chain
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


# ← This single line wires EU AI Act Article 14 governance into the chain
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
).with_config(callbacks=[warden_handler])

# ---------------------------------------------------------------------------
# Interactive loop
# ---------------------------------------------------------------------------

EXAMPLE_QUESTIONS = [
    "What is the refund policy?",
    "Do premium members get free shipping?",
    "When is customer support available?",
]


def run_query(question: str) -> str:
    try:
        return rag_chain.invoke(question)
    except WardenGateBlockedException as exc:
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

    try:
        status = warden.get_drift()
        print(f"  Warden status : {status.status} | drift={status.drift:.4f} | gate={status.gate}")
    except Exception as exc:
        print(f"  Warden status : UNREACHABLE ({exc})")
        print("  Proceeding in degraded mode — no governance checks will run.")
    print()

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        print(f"Q: {question}")
        print(f"A: {run_query(question)}\n")
        return

    for question in EXAMPLE_QUESTIONS:
        print(f"Q: {question}")
        print(f"A: {run_query(question)}\n")

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
