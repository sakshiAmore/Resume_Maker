from agents.resume_tailor import tailor_resume


def test_uploaded_resume_requires_source_citations(monkeypatch):
    monkeypatch.setattr(
        "agents.resume_tailor.generate_json",
        lambda *args, **kwargs: {
            "summary": "Python data professional",
            "experience_bullets": [{"chunk_id": "uploaded_0", "text": "Built Python dashboards"}],
            "project_bullets": [],
            "highlighted_skills": ["Python"],
        },
    )
    source = "Sakshi More\nData Analyst\nBuilt Python dashboards at Acme"

    result = tailor_resume("GenAI Engineer role", resume_text=source)

    assert result["_mode"] == "llm"
    assert result["profile"]["name"] == "Sakshi More"
