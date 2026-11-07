from agents.resume_tailor import tailor_resume


def test_uploaded_resume_skips_llm_and_preserves_source(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM must not rewrite uploaded resume content")

    monkeypatch.setattr("agents.resume_tailor.generate_json", fail_if_called)
    source = "Sakshi More\nData Analyst\nBuilt Python dashboards at Acme"

    result = tailor_resume("GenAI Engineer role", resume_text=source)

    assert result["_mode"] == "template"
    assert result["source_resume_text"] == source
    assert result["profile"]["name"] == "Sakshi More"
