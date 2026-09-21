from analyzer.ats_analyzer import analyze_ats


def test_ats_returns_expected_structure():
    text = """
    PRIYA SHARMA
    priya@example.com
    +91 98765 43210

    SUMMARY
    Software Engineer

    SKILLS
    Python
    Git

    EXPERIENCE
    - Developed backend APIs.

    EDUCATION
    Bachelor of Computer Applications
    """

    sections = {
        "summary": "Software Engineer",
        "skills": "Python\nGit",
        "experience": "- Developed backend APIs.",
        "education": "Bachelor of Computer Applications",
    }

    result = analyze_ats(text, sections)

    assert "score" in result
    assert "issues" in result
    assert "positives" in result
    assert "possible_multi_column" in result
    assert 0 <= result["score"] <= 100


def test_ats_detects_missing_contact_information():
    text = """
    SUMMARY
    Software Engineer

    SKILLS
    Python
    """

    sections = {
        "summary": "Software Engineer",
        "skills": "Python",
    }

    result = analyze_ats(text, sections)

    assert any("Email address was not detected" in issue for issue in result["issues"])
    assert any("Phone number was not detected" in issue for issue in result["issues"])


def test_ats_score_is_independent_of_job_description():
    text = """
    PRIYA SHARMA
    priya@example.com
    +91 98765 43210

    SUMMARY
    Software Engineer

    SKILLS
    Python

    EXPERIENCE
    - Developed applications.

    EDUCATION
    Bachelor of Computer Applications
    """

    sections = {
        "summary": "Software Engineer",
        "skills": "Python",
        "experience": "- Developed applications.",
        "education": "Bachelor of Computer Applications",
    }

    first = analyze_ats(text, sections)
    second = analyze_ats(text, sections)

    assert first["score"] == second["score"]