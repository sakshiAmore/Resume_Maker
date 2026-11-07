from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from resume_text_export import export_resume_text


def test_export_resume_text_contains_profile_and_sections(tmp_path):
    resume_data = {
        "profile": {"name": "Sakshi More", "email": "sakshi@example.com"},
        "summary": "Data Analyst and AI engineer",
        "experience_bullets": [{"text": "Built Python pipelines"}],
        "project_bullets": [{"text": "Developed RAG chatbot"}],
        "education": [{"degree": "BTech", "institution": "College", "dates": "2023-2026"}],
        "certifications": ["AWS"],
        "key_traits": ["Fast learner"],
        "skills_full": {"Languages": ["Python", "SQL"]},
    }
    output_path = tmp_path / "resume.txt"

    export_resume_text(resume_data, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "Sakshi More" in content
    assert "Professional Summary" in content
    assert "Experience" in content
    assert "Projects" in content
    assert "Skills" in content
