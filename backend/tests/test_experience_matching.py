import pytest

from analyzer.scoring import match_experience


def test_experience_meets_requirement():
    resume = {
        "experience_years": 4.0,
        "experience_confidence": "high",
    }

    jd = {
        "required_years": 3.0,
    }

    result = match_experience(resume, jd)

    assert result["score"] == 100
    assert result["resume_years"] == 4.0
    assert result["required_years"] == 3.0
    assert "Meets the minimum experience requirement" in result["status"]


def test_experience_exactly_meets_requirement():
    resume = {
        "experience_years": 3.0,
        "experience_confidence": "high",
    }

    jd = {
        "required_years": 3.0,
    }

    result = match_experience(resume, jd)

    assert result["score"] == 100
    assert "Meets the minimum experience requirement" in result["status"]


def test_experience_below_requirement():
    resume = {
        "experience_years": 2.92,
        "experience_confidence": "high",
    }

    jd = {
        "required_years": 3.0,
    }

    result = match_experience(resume, jd)

    assert result["score"] < 100
    assert result["score"] == 97
    assert "Below the minimum experience requirement" in result["status"]
    assert result["resume_years"] == 2.92
    assert result["required_years"] == 3.0


def test_experience_far_below_requirement():
    resume = {
        "experience_years": 1.0,
    }

    jd = {
        "required_years": 4.0,
    }

    result = match_experience(resume, jd)

    assert result["score"] == 25
    assert "Below the minimum experience requirement" in result["status"]


def test_no_jd_experience_requirement_returns_none_score():
    resume = {
        "experience_years": 3.0,
    }

    jd = {
        "required_years": None,
    }

    result = match_experience(resume, jd)

    assert result["score"] is None
    assert result["required_years"] is None
    assert ("could not be determined" in result["status"].lower() or "no explicit minimum experience requirement" in result["status"].lower())

def test_no_resume_experience_returns_none_score():
    resume = {
        "experience_years": None,
    }

    jd = {
        "required_years": 3.0,
    }

    result = match_experience(resume, jd)

    assert result["score"] is None
    assert result["resume_years"] is None
    assert result["required_years"] == 3.0
    assert "could not be determined reliably" in result["status"]


def test_experience_confidence_is_preserved():
    resume = {
        "experience_years": 5.0,
        "experience_confidence": "medium",
    }

    jd = {
        "required_years": 3.0,
    }

    result = match_experience(resume, jd)

    assert result["confidence"] == "medium"


@pytest.mark.parametrize(
    "resume_years, required_years, expected_score",
    [
        (2.0, 4.0, 50),
        (2.5, 5.0, 50),
        (1.5, 3.0, 50),
        (4.0, 5.0, 80),
        (4.9, 5.0, 98),
    ],
)
def test_experience_partial_scores(
    resume_years,
    required_years,
    expected_score,
):
    resume = {
        "experience_years": resume_years,
    }

    jd = {
        "required_years": required_years,
    }

    result = match_experience(resume, jd)

    assert result["score"] == expected_score
    assert result["score"] < 100