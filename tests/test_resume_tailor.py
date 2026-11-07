import agents.resume_tailor as resume_tailor


def test_incomplete_model_response_uses_template_fallback(monkeypatch):
    monkeypatch.setattr(resume_tailor, "generate_json", lambda *args, **kwargs: {"error": "missing summary"})

    result = resume_tailor.tailor_resume(
        "Python data engineer",
        resume_text="Sakshi More\nPython developer with SQL experience",
    )

    assert result["_mode"] == "template"
    assert result["summary"]
    assert result["_generation_error"] == "missing summary"
