import pytest

from analyzer.jd_analyzer import (
    analyze_jd,
    extract_education,
    extract_experience_requirement,
    extract_general_requirements,
    extract_requirement_keywords,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Minimum 3 years of experience required.", 3.0),
        ("At least 2 years of experience required.", 2.0),
        ("Requires 4+ years of experience.", 4.0),
        ("Requires 1-3 years of experience.", 1.0),
        ("Requires 2–4 years of experience.", 2.0),
        ("Requires 3 to 5 years of experience.", 3.0),
        ("Minimum 3-4 years of professional experience.", 3.0),
    ],
)
def test_extract_experience_requirement(text, expected):
    assert extract_experience_requirement(text) == expected


def test_experience_requirement_none_when_absent():
    text = "We are looking for a cloud engineer with Python experience."
    assert extract_experience_requirement(text) is None


def test_bachelors_degree_detection():
    result = extract_education(
        "Bachelor's degree in Computer Science or comparable qualification."
    )
    assert result


def test_be_does_not_match_normal_word_be():
    result = extract_education(
        "The candidate should be comfortable working independently."
    )
    assert "BE" not in result


def test_general_requirement_detection():
    result = extract_general_requirements(
        "Experience with monitoring, incident response and root cause analysis."
    )
    assert "monitoring" in result
    assert "incident management" in result
    assert "root cause analysis" in result


def test_generic_requirement_keywords_work_for_unknown_domain():
    result = extract_requirement_keywords(
        "Prepare monthly financial statements and reconcile general ledger accounts."
    )
    assert result


def test_analyze_jd_returns_structured_result():
    jd = """
    DevOps Engineer

    Requirements:
    Minimum 3 years of professional experience.
    Experience with Azure and Python.
    Bachelor's degree in Computer Science.

    Preferred Qualifications:
    Kubernetes experience is preferred.
    """

    result = analyze_jd(jd)

    assert result["text"]
    assert "required_skills" in result
    assert "preferred_skills" in result
    assert "requirement_lines" in result
    assert "required_years" in result
    assert "education" in result
    assert result["required_years"] == 3.0


def test_analyze_jd_rejects_empty_input():
    with pytest.raises(ValueError, match="Job description is empty"):
        analyze_jd("")