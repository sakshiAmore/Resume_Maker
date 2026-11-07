import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import generate

SYSTEM = (
    "You are a cold outreach email agent. Write a short (under 150 words) email to a recruiter "
    "or hiring manager. Structure: subject line + 1-line hook + 2-line relevant achievement + clear ask. "
    "Only use provided verified facts. Output format:\nSubject: <subject>\n\n<body>"
)


def generate_cold_email(jd_text: str, tailored_resume: dict, company: str = "", role_title: str = "") -> str:
    experience_bullets = tailored_resume.get("experience_bullets", []) or []
    facts = f"Top achievement: {experience_bullets[0].get('text', '') if experience_bullets else ''}"
    prompt = (
        f"Job description:\n{jd_text}\n\nCompany: {company or 'the company'}\nRole: {role_title or 'the role'}\n\n"
        f"Verified candidate facts:\n{facts}\n\nWrite the email."
    )
    email = generate(SYSTEM, prompt, max_tokens=300)

    if email.startswith("[MOCK MODE"):
        name = tailored_resume["profile"]["name"]
        top = experience_bullets[0].get("text", "") if experience_bullets else "relevant experience"
        email = (
            f"[TEMPLATE MODE — set GROQ_API_KEY for a properly written email]\n\n"
            f"Subject: {role_title or 'Application'} — {name}\n\n"
            f"Hi,\n\nI came across the {role_title or '[Role]'} opening at {company or '[Company]'} and wanted to reach out directly. "
            f"{top}\n\nWould you be open to a short call this week to discuss the role?\n\nBest,\n{name}"
        )
    return email
