import sys, os, json, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import generate_json
from retriever import TfidfRetriever, Chunk
from ats_scorer import calculate_ats_score

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


def _profile_from_resume(text: str, fallback: dict) -> dict:
    """Use contact details from the uploaded resume instead of the local fallback."""
    profile = dict(fallback)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        profile["name"] = lines[0][:100]
    email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    phone = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text)
    linkedin = re.search(r"https?://(?:www\.)?linkedin\.com/\S+", text, re.IGNORECASE)
    github = re.search(r"https?://(?:www\.)?github\.com/\S+", text, re.IGNORECASE)
    if email:
        profile["email"] = email.group(0)
    if phone:
        profile["phone"] = phone.group(0).strip()
    if linkedin:
        profile["linkedin"] = linkedin.group(0).rstrip(".,")
    if github:
        profile["github"] = github.group(0).rstrip(".,")
    return profile


def _template_result(resume_text: str, kb: dict, exp_chunks, proj_chunks, skill_chunks, reason: str = "") -> dict:
    result = {
        "summary": resume_text.strip()[:500] if resume_text.strip() else kb["summary_source"],
        "experience_bullets": [{"chunk_id": c.id, "text": c.text} for c in exp_chunks],
        "project_bullets": [{"chunk_id": c.id, "text": c.text} for c in proj_chunks],
        "highlighted_skills": [c.meta.get("category") for c in skill_chunks if c.meta.get("category")],
        "_mode": "template",
    }
    if reason:
        result["_generation_error"] = reason
    return result


def tailor_resume(jd_text: str, kb_path: str = "knowledge_base.json", k: int = 12, resume_text: str = "") -> dict:
    retriever = TfidfRetriever(kb_path)
    if resume_text.strip():
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        retriever.chunks = [
            Chunk(f"uploaded_{index}", line, "experience" if index % 2 == 0 else "project", {})
            for index, line in enumerate(lines)
        ]
        retriever._build_index()
    chunks = retriever.retrieve(jd_text, k=k)
    exp_chunks, proj_chunks, skill_chunks = _group_by_source(chunks)

    with open(kb_path, encoding="utf-8") as f:
        kb = json.load(f)
    source_text = resume_text.strip() or json.dumps(kb)

    retrieved_text = "\n".join(f"- [{c.id}] ({c.source}) {c.text}" for c in chunks)

    result = generate_json(
        SYSTEM,
        f"Job description:\n{jd_text}\n\n"
        f"Uploaded resume source (use this as the only candidate source):\n{source_text}\n\n"
        f"Retrieved candidate facts (only use these, cite chunk IDs):\n{retrieved_text}\n\n"
        'Return JSON: {"summary": str, "experience_bullets": [{"chunk_id": str, "text": str}], '
        '"project_bullets": [{"chunk_id": str, "text": str}], "highlighted_skills": [str]}',
    )

    required_keys = {"summary", "experience_bullets", "project_bullets", "highlighted_skills"}
    if result.get("mock"):
        result = _template_result(resume_text, kb, exp_chunks, proj_chunks, skill_chunks)
    elif (
        not isinstance(result, dict)
        or not required_keys.issubset(result)
        or not isinstance(result.get("summary"), str)
        or not isinstance(result.get("experience_bullets"), list)
        or not isinstance(result.get("project_bullets"), list)
    ):
        result = _template_result(
            resume_text,
            kb,
            exp_chunks,
            proj_chunks,
            skill_chunks,
            result.get("error", "The model returned incomplete resume data.")
            if isinstance(result, dict)
            else "The model returned an invalid resume response.",
        )
    else:
        result["_mode"] = "llm"

    # Keep the existing document schema for compatibility with the PDF builder.
    result["profile"] = _profile_from_resume(resume_text, kb["profile"]) if resume_text.strip() else kb["profile"]
    result["education"] = kb["education"]
    result["certifications"] = kb["certifications"]
    result["key_traits"] = kb["key_traits"]
    result["skills_full"] = kb["skills"]
    result["ats"] = calculate_ats_score(
        "\n".join(item.get("text", "") for item in result.get("experience_bullets", []) + result.get("project_bullets", [])),
        jd_text,
        result.get("highlighted_skills", []),
    )
    return result


if __name__ == "__main__":
    sample_jd = """
    We are hiring a GenAI Engineer with strong experience in LangChain, RAG pipelines,
    and vector databases like FAISS. Must have Python and SQL skills, and experience
    building production-grade LLM agents and anomaly detection for fraud/compliance use cases.
    """
    out = tailor_resume(sample_jd)
    print(json.dumps(out, indent=2))
