"""
retriever.py — lightweight retrieval layer over the knowledge_base.json

This keeps the pipeline dependency-light and avoids the broken scipy/scikit-learn stack
on the current environment while still providing TF-IDF-like relevance ranking.
"""

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import List

TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class Chunk:
    id: str
    text: str
    source: str          # "experience" | "project" | "skill"
    meta: dict           # company/role/project name etc, for citing back to source


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


def _tokenize(text: str) -> List[str]:
    return TOKEN_RE.findall(text.lower())


def load_chunks(kb_path: str = "knowledge_base.json") -> List[Chunk]:
    with open(_resolve_path(kb_path), encoding="utf-8") as handle:
        kb = json.load(handle)

    chunks: List[Chunk] = []

    for exp in kb["experience"]:
        for bullet in exp["bullets"]:
            chunks.append(Chunk(
                id=bullet["id"],
                text=f"{exp['role']} at {exp['company']}: {bullet['text']}",
                source="experience",
                meta={"company": exp["company"], "role": exp["role"], "dates": exp["dates"], "tags": bullet.get("tags", [])}
            ))

    for proj in kb["projects"]:
        for bullet in proj["bullets"]:
            chunks.append(Chunk(
                id=bullet["id"],
                text=f"{proj['name']} ({proj['stack']}): {bullet['text']}",
                source="project",
                meta={"project": proj["name"], "stack": proj["stack"], "tags": bullet.get("tags", [])}
            ))

    for category, items in kb["skills"].items():
        chunks.append(Chunk(
            id=f"skill_{category.lower().replace(' ', '_').replace('/', '_')}",
            text=f"{category}: {', '.join(items)}",
            source="skill",
            meta={"category": category, "items": items}
        ))

    return chunks


class TfidfRetriever:
    """A dependency-light cosine similarity retriever using built-in Python logic."""

    def __init__(self, kb_path: str = "knowledge_base.json"):
        self.chunks = load_chunks(kb_path)
        self._build_index()

    def _build_index(self) -> None:
        corpus = [chunk.text for chunk in self.chunks]
        document_frequencies: Counter[str] = Counter()
        for document in corpus:
            document_frequencies.update(set(_tokenize(document)))

        self.idf = {
            term: math.log((1 + len(corpus)) / (1 + document_frequencies[term])) + 1.0
            for term in document_frequencies
        }
        self.doc_vectors = []
        for document in corpus:
            counts = Counter(_tokenize(document))
            self.doc_vectors.append({term: counts[term] * self.idf.get(term, 1.0) for term in counts})

    def retrieve(self, query: str, k: int = 6) -> List[Chunk]:
        q_counts = Counter(_tokenize(query))
        q_vector = {term: q_counts[term] * self.idf.get(term, 1.0) for term in q_counts}
        score_pairs = []

        for index, doc_vector in enumerate(self.doc_vectors):
            score = 0.0
            for term, q_weight in q_vector.items():
                if term in doc_vector:
                    score += q_weight * doc_vector[term]

            if score <= 0:
                continue

            norm_q = math.sqrt(sum(weight * weight for weight in q_vector.values()))
            norm_d = math.sqrt(sum(weight * weight for weight in doc_vector.values()))
            if norm_q and norm_d:
                score /= (norm_q * norm_d)
            score_pairs.append((score, index))

        score_pairs.sort(reverse=True)
        return [self.chunks[index] for _, index in score_pairs[:k]]


if __name__ == "__main__":
    retriever = TfidfRetriever()
    jd = "Looking for an ML engineer experienced in RAG, LangChain, and anomaly detection for fraud"
    results = retriever.retrieve(jd, k=5)
    print(f"Query: {jd}\n")
    for chunk in results:
        print(f"  [{chunk.source}] {chunk.text}")
