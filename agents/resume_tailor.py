import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import generate_json
from retriever import TfidfRetriever, Chunk

SYSTEM = (
    "You are a resume tailoring agent. You will be given: (1) a job description, "
    "(2) a set of RETRIEVED, VERIFIED facts about the candidate's real experience/projects/skills. "
    "Rewrite the candidate's summary and select/rephrase bullets to mirror the JD's language and "
    "keywords, WITHOUT inventing any skill, metric, or achievement that is not present in the "
    "retrieved facts. Every bullet in your output must be traceable to one of the retrieved chunk IDs."
)


def _group_by_source(chunks):
    exp, proj, skill = [], [], []
    for c in chunks:
        (exp if c.source == "experience" else proj if c.source == "project" else skill).append(c)
    return exp, proj, skill


def tailor_resume(jd_text: str, kb_path: str = "knowledge_base.json", k: int = 12) -> dict:
    retriever = TfidfRetriever(kb_path)
    chunks = retriever.retrieve(jd_text, k=k)
    exp_chunks, proj_chunks, skill_chunks = _group_by_source(chunks)

    with open(kb_path) as f:
        kb = json.load(f)

    retrieved_text = "\n".join(f"- [{c.id}] ({c.source}) {c.text}" for c in chunks)

    result = generate_json(
        SYSTEM,
        f"Job description:\n{jd_text}\n\n"
        f"Retrieved candidate facts (only use these, cite chunk IDs):\n{retrieved_text}\n\n"
        'Return JSON: {"summary": str, "experience_bullets": [{"chunk_id": str, "text": str}], '
        '"project_bullets": [{"chunk_id": str, "text": str}], "highlighted_skills": [str]}',
    )

    if result.get("mock"):
        # Template fallback: use retrieved chunks verbatim (still ATS-relevant, just not JD-reworded)
        result = {
            "summary": kb["summary_source"],
            "experience_bullets": [{"chunk_id": c.id, "text": c.text} for c in exp_chunks],
            "project_bullets": [{"chunk_id": c.id, "text": c.text} for c in proj_chunks],
            "highlighted_skills": [c.meta.get("category") for c in skill_chunks],
            "_mode": "template",
        }
    else:
        result["_mode"] = "llm"

    # Attach full profile/education/certs (these don't need tailoring)
    result["profile"] = kb["profile"]
    result["education"] = kb["education"]
    result["certifications"] = kb["certifications"]
    result["key_traits"] = kb["key_traits"]
    result["skills_full"] = kb["skills"]
    return result


if __name__ == "__main__":
    sample_jd = """
    We are hiring a GenAI Engineer with strong experience in LangChain, RAG pipelines,
    and vector databases like FAISS. Must have Python and SQL skills, and experience
    building production-grade LLM agents and anomaly detection for fraud/compliance use cases.
    """
    out = tailor_resume(sample_jd)
    print(json.dumps(out, indent=2))
