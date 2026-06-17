"""
LangGraph RAG chatbot with Spec-Drift Chronometer governance.

Shows that the same WardenCallbackHandler used in rag_chatbot.py works
identically with a LangGraph graph — the callback fires on graph entry
the same way it fires on LCEL chain entry.

Setup:
    cp .env.example .env
    # Fill in OPENAI_API_KEY in .env
    pip install -r requirements.txt
    python langgraph_example.py
"""

from __future__ import annotations
import os
import logging
from typing import TypedDict, List
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")

WARDEN_API_URL = os.environ.get("WARDEN_API_URL", "http://localhost:8000")
WARDEN_DASH_URL = os.environ.get("WARDEN_DASH_URL", "http://localhost:3000")

# ---------------------------------------------------------------------------
# Warden governance — identical setup to rag_chatbot.py
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
# Models and vector store
# ---------------------------------------------------------------------------

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

SAMPLE_DOCS = [
    "Our refund policy allows returns within 30 days of purchase with a valid receipt.",
    "Premium members receive free shipping on all orders over €50.",
    "Customer support is available Monday to Friday, 09:00–18:00 CET.",
    "All personal data is processed in EU data centres in compliance with GDPR.",
]

embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

docs = [Document(page_content=text) for text in SAMPLE_DOCS]
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# ---------------------------------------------------------------------------
# LangGraph RAG graph
# ---------------------------------------------------------------------------

from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class RAGState(TypedDict):
    question: str
    documents: List[Document]
    answer: str


def retrieve(state: RAGState) -> dict:
    return {"documents": retriever.invoke(state["question"])}


def generate(state: RAGState) -> dict:
    context = "\n\n".join(doc.page_content for doc in state["documents"])
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer using only this context:\n\n{context}"),
        ("human", "{question}"),
    ])
    chain = prompt | llm | StrOutputParser()
    return {"answer": chain.invoke({"context": context, "question": state["question"]})}


builder = StateGraph(RAGState)
builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)
builder.set_entry_point("retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)
graph = builder.compile()

# ← The same single line that governs the LCEL chain also governs this graph
governed_graph = graph.with_config(callbacks=[warden_handler])

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

EXAMPLE_QUESTIONS = [
    "What is the refund policy?",
    "Do premium members get free shipping?",
]


def run_query(question: str) -> str:
    try:
        result = governed_graph.invoke({"question": question, "documents": [], "answer": ""})
        return result["answer"]
    except WardenGateBlockedException as exc:
        return str(exc)
    except Exception as exc:
        return f"Error: {exc}"


if __name__ == "__main__":
    print("=" * 62)
    print("  LangGraph RAG — Governed by Spec-Drift Chronometer")
    print("=" * 62)
    print(f"  Warden API : {WARDEN_API_URL}")
    print(f"  Dashboard  : {WARDEN_DASH_URL}\n")

    try:
        status = warden.get_drift()
        print(f"  Warden: {status.status} | drift={status.drift:.4f} | gate={status.gate}\n")
    except Exception as exc:
        print(f"  Warden: UNREACHABLE ({exc}) — proceeding in degraded mode.\n")

    for question in EXAMPLE_QUESTIONS:
        print(f"Q: {question}")
        print(f"A: {run_query(question)}\n")
