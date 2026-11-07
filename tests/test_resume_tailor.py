import agents.resume_tailor as resume_tailor


def test_uploaded_resume_falls_back_when_model_response_is_invalid(monkeypatch):
    monkeypatch.setattr(resume_tailor, "generate_json", lambda *args, **kwargs: {"error": "invalid"})

    result = resume_tailor.tailor_resume(
        "Python data engineer",
        resume_text="Sakshi More\nPython developer with SQL experience",
    )

    assert result["_mode"] == "template"
    assert result["summary"]
    assert result["experience_bullets"][0]["text"].startswith("Sakshi More")
