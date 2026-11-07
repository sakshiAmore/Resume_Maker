from agents.jd_analyzer import extract_job_details


def test_extract_job_posting_details():
    details = extract_job_details(
        "Data Engineer at Acme. 3+ years of experience. "
        "Posted on 7 November 2026. Apply by 30 November 2026. "
        "Location: Mumbai. Employment type: Full-time."
    )

    assert details["experience"].startswith("3+ years")
    assert details["posted_date"].startswith("7 November")
    assert details["application_deadline"].startswith("30 November")
    assert details["location"] == "Mumbai"
    assert details["employment_type"].lower() == "full-time"
