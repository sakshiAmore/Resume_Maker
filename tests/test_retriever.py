from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from retriever import TfidfRetriever


def test_tfidf_retriever_returns_results():
    retriever = TfidfRetriever(kb_path="knowledge_base.json")
    chunks = retriever.retrieve("LangChain RAG chatbot fraud detection", k=5)
    assert chunks
    assert any(chunk.source in {"experience", "project"} for chunk in chunks)
