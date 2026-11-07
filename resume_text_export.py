import os
from typing import Any, Dict


def _clean_text(value: str) -> str:
    return str(value or "").replace("\n", " ").strip()


def export_resume_text(resume_data: Dict[str, Any], output_path: str | os.PathLike[str] | None = None) -> str:
    profile = resume_data.get("profile", {})
    lines = []
    lines.append(profile.get("name", "Your Name"))
    lines.append(_clean_text(profile.get("location", "")))
    lines.append(f"Phone: {_clean_text(profile.get('phone', ''))}")
    lines.append(f"Email: {_clean_text(profile.get('email', ''))}")
    lines.append(f"LinkedIn: {_clean_text(profile.get('linkedin', ''))}")
    lines.append(f"GitHub: {_clean_text(profile.get('github', ''))}")
    lines.append("")
    lines.append("Professional Summary")
    lines.append(_clean_text(resume_data.get("summary", "")))
    lines.append("")
    lines.append("Skills")
    for category, items in (resume_data.get("skills_full") or {}).items():
        lines.append(f"{category}: {', '.join(items)}")
    lines.append("")
    lines.append("Experience")
    for bullet in resume_data.get("experience_bullets", []) or []:
        lines.append(f"- {_clean_text(bullet.get('text', ''))}")
    lines.append("")
    lines.append("Projects")
    for bullet in resume_data.get("project_bullets", []) or []:
        lines.append(f"- {_clean_text(bullet.get('text', ''))}")
    lines.append("")
    lines.append("Education")
    for item in resume_data.get("education", []) or []:
        lines.append(f"- {_clean_text(item.get('degree', ''))} | {_clean_text(item.get('institution', ''))} | {_clean_text(item.get('dates', ''))}")
    lines.append("")
    lines.append("Certifications")
    for cert in resume_data.get("certifications", []) or []:
        lines.append(f"- {_clean_text(cert)}")
    lines.append("")
    lines.append("Key Traits")
    lines.append(", ".join(resume_data.get("key_traits", []) or []))

    content = "\n".join(lines)
    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(content)
    return content
