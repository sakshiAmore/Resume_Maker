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


def _verified_skills(skills: dict, source_text: str) -> dict:
    source = source_text.lower()
    verified = {}
    for category, items in (skills or {}).items():
        kept = [item for item in items if isinstance(item, str) and item.lower() in source]
        if kept:
            verified[category] = kept
    return verified


def _template_result(resume_text: str, kb: dict, exp_chunks, proj_chunks, skill_chunks, reason: str = "") -> dict:
    source_lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    source_bullets = [
        {"chunk_id": f"uploaded_{index}", "text": line}
        for index, line in enumerate(source_lines)
    ]
    result = {
        "summary": resume_text.strip()[:500] if resume_text.strip() else kb["summary_source"],
        "experience_bullets": source_bullets if resume_text.strip() else [{"chunk_id": c.id, "text": c.text} for c in exp_chunks],
        "project_bullets": [] if resume_text.strip() else [{"chunk_id": c.id, "text": c.text} for c in proj_chunks],
        "highlighted_skills": [c.meta.get("category") for c in skill_chunks if c.meta.get("category")],
        "_mode": "template",
    }
    if reason:
        result["_generation_error"] = reason
    return result


def _uploaded_result(jd_text: str, resume_text: str, chunks, kb: dict) -> dict:
    """Tailor uploaded facts while requiring every result item to cite source text."""
    retrieved_text = "\n".join(f"- [{c.id}] {c.text}" for c in chunks)
    source_ids = {c.id for c in chunks}
    result = generate_json(
        SYSTEM,
        f"Job description:\n{jd_text}\n\n"
        f"Verified uploaded resume:\n{resume_text}\n\n"
        f"Relevant source lines:\n{retrieved_text}\n\n"
        "Tailor the resume for this job. You may reorder, shorten, and rephrase "
        "only the verified source lines. Do not add any skill, employer, title, "
        "date, degree, metric, certification, or technology from the job description. "
        "Every experience/project bullet must cite one source line ID. Return concise "
        'ATS-friendly content as JSON: {"summary": str, '
        '"experience_bullets": [{"chunk_id": str, "text": str}], '
        '"project_bullets": [{"chunk_id": str, "text": str}], '
        '"highlighted_skills": [str], "skills_full": {"category": [str]}, '
        '"education": [{"degree": str, "institution": str, "dates": str}], '
        '"certifications": [str]}',
    )
    required = {"summary", "experience_bullets", "project_bullets", "highlighted_skills"}
    if not isinstance(result, dict) or not required.issubset(result):
        return _template_result(resume_text, kb, chunks, [], [], "Incomplete model response.")
    bullets = result["experience_bullets"] + result["project_bullets"]
    if not all(
        isinstance(item, dict)
        and item.get("chunk_id") in source_ids
        and isinstance(item.get("text"), str)
        and item["text"].strip()
        for item in bullets
    ):
        return _template_result(resume_text, kb, chunks, [], [], "Model returned unsupported resume facts.")
    result["_mode"] = "llm"
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
    uploaded_chunks = retriever.chunks if resume_text.strip() else chunks
    exp_chunks, proj_chunks, skill_chunks = _group_by_source(chunks)

    with open(kb_path, encoding="utf-8") as f:
        kb = json.load(f)
    source_text = resume_text.strip() or json.dumps(kb)

    retrieved_text = "\n".join(f"- [{c.id}] ({c.source}) {c.text}" for c in chunks)

    if resume_text.strip():
        result = _uploaded_result(jd_text, resume_text, uploaded_chunks, kb)
    else:
        result = None

    if result is None:
        result = generate_json(
        SYSTEM,
        f"Job description:\n{jd_text}\n\n"
        f"Uploaded resume source (use this as the only candidate source):\n{source_text}\n\n"
        f"Retrieved candidate facts (only use these, cite chunk IDs):\n{retrieved_text}\n\n"
        'Return JSON: {"summary": str, "experience_bullets": [{"chunk_id": str, "text": str}], '
        '"project_bullets": [{"chunk_id": str, "text": str}], "highlighted_skills": [str], '
        '"education": [{"degree": str, "institution": str, "dates": str}], '
        '"certifications": [str], "skills_full": {"category": [str]}}',
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
    elif result.get("_mode") == "llm":
        pass
    elif result.get("_mode") == "template":
        pass
    else:
        result["_mode"] = "llm"

    # Keep the existing document schema for compatibility with the PDF builder.
    result["profile"] = (
        _profile_from_resume(
            resume_text,
            {"name": "", "location": "", "phone": "", "email": "", "linkedin": "", "github": ""},
        )
        if resume_text.strip()
        else kb["profile"]
    )
    result["education"] = result.get("education") or kb["education"]
    result["certifications"] = result.get("certifications") or kb["certifications"]
    result["key_traits"] = kb["key_traits"]
    result["skills_full"] = (
        _verified_skills(result.get("skills_full"), resume_text)
        if resume_text.strip()
        else result.get("skills_full") or kb["skills"]
    )
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
