import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from llm_client import generate_json

SYSTEM = (
    "You are a JD analysis agent. Given a job description, extract the role title, "
    "company name (if present), must-have skills, nice-to-have skills, and 5-10 ATS "
    "keywords a resume should mirror. Be precise, do not invent requirements not in the text."
)


def extract_job_details(jd_text: str) -> dict:
    """Extract clearly labelled job-posting facts without guessing."""
    text = " ".join((jd_text or "").split())

    def labelled(pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip(" .,:;|-") if match else ""

    experience = labelled(r"(?:requires?|minimum|required)\s+(?:at least\s+)?(\d+\+?\s*(?:years?|months?)[^.;,]*)")
    if not experience:
        experience = labelled(r"(\d+\+?\s*(?:years?|months?)\s+(?:of\s+)?experience)")
    posted = labelled(r"(?:posted|published|listed)\s*(?:on|date)?\s*[:\-]?\s*([A-Za-z0-9 ,/\-]+?)(?=[.;]|\s+(?:apply|application|deadline|closing|last date)\b|$)")
    deadline = labelled(r"(?:last date|deadline|closing date|apply by|applications close)\s*[:\-]?\s*([A-Za-z0-9 ,/\-]+?)(?=[.;]|$)")
    location = labelled(r"(?:location|based in|work location)\s*[:\-]?\s*([^.;,|]+)")
    employment_type = labelled(r"(?:employment type|job type|work type)\s*[:\-]?\s*(full[- ]time|part[- ]time|contract|internship|temporary|remote|hybrid|on[- ]site)")
    return {
        "experience": experience or "Not specified",
        "posted_date": posted or "Not specified",
        "application_deadline": deadline or "Not specified",
        "location": location or "Not specified",
        "employment_type": employment_type or "Not specified",
    }


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
        result = {
            "role_title": "Unknown (template mode — set GROQ_API_KEY for real extraction)",
            "company": "Unknown",
            "must_have_skills": top_keywords[:5],
            "nice_to_have_skills": top_keywords[5:10],
            "ats_keywords": top_keywords,
            "_mode": "template",
        }
    elif not isinstance(result, dict):
        result = {}
    result["_mode"] = result.get("_mode", "llm")
    result["job_details"] = extract_job_details(jd_text)
    return result


if __name__ == "__main__":
    sample_jd = """
    We are hiring a GenAI Engineer with strong experience in LangChain, RAG pipelines,
    and vector databases like FAISS. Must have Python and SQL skills, and experience
    building production-grade LLM agents. AWS experience is a plus.
    """
    print(analyze(sample_jd))
