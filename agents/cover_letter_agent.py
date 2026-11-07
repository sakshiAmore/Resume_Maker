import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import generate

SYSTEM = (
    "You are a cover letter writing agent. Write a concise, natural, non-generic 3-4 paragraph "
    "cover letter using ONLY the provided verified candidate facts. Never invent experience. "
    "Structure: opening hook -> 2 relevant achievements mapped to the JD -> why this company -> "
    "closing call to action. No purple prose, no cliches like 'I am writing to express my interest'."
)


def generate_cover_letter(jd_text: str, tailored_resume: dict, company: str = "", role_title: str = "") -> str:
    summary = tailored_resume.get("summary", "")
    experience_bullets = tailored_resume.get("experience_bullets", []) or []
    project_bullets = tailored_resume.get("project_bullets", []) or []
    facts = (
        f"Summary: {summary}\n"
        f"Experience highlights: {[b.get('text', '') for b in experience_bullets]}\n"
        f"Project highlights: {[b.get('text', '') for b in project_bullets]}\n"
    )
    prompt = (
        f"Job description:\n{jd_text}\n\n"
        f"Company: {company or 'the company'}\nRole: {role_title or 'the role'}\n\n"
        f"Verified candidate facts:\n{facts}\n\n"
        "Write the cover letter body only (no letterhead/date/address block)."
    )
    letter = generate(SYSTEM, prompt, max_tokens=800)

    if letter.startswith("[MOCK MODE"):
        # Template fallback so the pipeline still produces a usable draft
        exp_line = experience_bullets[0].get("text", "") if experience_bullets else ""
        proj_line = project_bullets[0].get("text", "") if project_bullets else ""
        letter = (
            f"[TEMPLATE MODE — set GROQ_API_KEY for a properly written letter]\n\n"
            f"I'm applying for the {role_title or '[Role]'} position at {company or '[Company]'}. "
            f"{summary}\n\n"
            f"In my most recent role, {exp_line}. I've also {proj_line.lower()}.\n\n"
            f"I'd welcome the chance to bring this experience to {company or '[Company]'} and discuss "
            f"how it fits your team's current needs.\n\n"
            f"Best regards,\n{tailored_resume['profile']['name']}"
        )
    return letter
