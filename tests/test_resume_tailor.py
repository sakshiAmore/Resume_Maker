import agents.resume_tailor as resume_tailor


def test_uploaded_resume_uses_deterministic_fallback(monkeypatch):
    monkeypatch.setattr(resume_tailor, "generate_json", lambda *args, **kwargs: {"error": "must not be called"})

    result = resume_tailor.tailor_resume(
        "Python data engineer",
        resume_text="Sakshi More\nPython developer with SQL experience",
    )

    assert result["_mode"] == "template"
    assert result["summary"]
    assert result["source_resume_text"].startswith("Sakshi More")
