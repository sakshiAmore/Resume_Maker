import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from llm_client import generate_json

SYSTEM = (
    "You are a JD analysis agent. Given a job description, extract the role title, "
    "company name (if present), must-have skills, nice-to-have skills, and 5-10 ATS "
    "keywords a resume should mirror. Be precise, do not invent requirements not in the text."
)


def analyze(jd_text: str) -> dict:
    result = generate_json(
        SYSTEM,
        f"Job description:\n\n{jd_text}\n\n"
        'Return JSON with keys: "role_title", "company", "must_have_skills" (list), '
        '"nice_to_have_skills" (list), "ats_keywords" (list).',
    )
    if result.get("mock"):
        # Template fallback: crude keyword extraction so the pipeline still runs end-to-end
        words = re.findall(r"[A-Za-z][A-Za-z+\-.#]{2,}", jd_text)
        stop = {"the", "and", "for", "with", "you", "our", "will", "are", "this", "that",
                "have", "your", "job", "role", "work", "team", "who", "can", "able"}
        freq = {}
        for w in words:
            wl = w.lower()
            if wl in stop or len(wl) < 3:
                continue
            freq[wl] = freq.get(wl, 0) + 1
        top_keywords = sorted(freq, key=freq.get, reverse=True)[:10]
        return {
            "role_title": "Unknown (template mode — set GROQ_API_KEY for real extraction)",
            "company": "Unknown",
            "must_have_skills": top_keywords[:5],
            "nice_to_have_skills": top_keywords[5:10],
            "ats_keywords": top_keywords,
            "_mode": "template",
        }
    result["_mode"] = "llm"
    return result


if __name__ == "__main__":
    sample_jd = """
    We are hiring a GenAI Engineer with strong experience in LangChain, RAG pipelines,
    and vector databases like FAISS. Must have Python and SQL skills, and experience
    building production-grade LLM agents. AWS experience is a plus.
    """
    print(analyze(sample_jd))
