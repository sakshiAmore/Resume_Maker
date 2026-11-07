from pathlib import Path

from ats_scorer import calculate_ats_score
from resume_parser import extract_resume_text


def test_extract_plain_text_resume(tmp_path: Path):
    resume = tmp_path / "resume.txt"
    resume.write_text("Sakshi More\nsakshi@example.com\nPython and SQL experience", encoding="utf-8")

    assert "sakshi@example.com" in extract_resume_text(str(resume))


def test_ats_score_has_ninety_percent_floor():
    result = calculate_ats_score("Python", "Python SQL", ["Python", "SQL"])

    assert result["score"] >= 90
    assert "python" in result["matched_keywords"]
