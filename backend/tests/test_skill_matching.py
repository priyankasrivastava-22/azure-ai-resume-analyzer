import pytest

from analyzer.scoring import (
    build_resume_skill_set,
    match_alternative_groups,
    match_skills,
    skill_matches,
)


def test_build_resume_skill_set_normalizes_values():
    resume = {
        "skills": ["Python", " Azure ", "PYTHON", "Terraform"]
    }

    result = build_resume_skill_set(resume)

    assert "python" in result
    assert "azure" in result
    assert "terraform" in result


@pytest.mark.parametrize(
    "resume_skills, required_skill, expected",
    [
        ({"python"}, "Python", True),
        ({"azure"}, "Azure", True),
        ({"kusto"}, "KQL", True),
        ({"kql"}, "Kusto", True),
        ({"powerbi"}, "Power BI", True),
        ({"nodejs"}, "Node.js", True),
        ({"restful api"}, "REST API", True),
        ({"docker"}, "Kubernetes", False),
    ],
)
def test_skill_matches_known_equivalents(
    resume_skills,
    required_skill,
    expected,
):
    assert skill_matches(
        resume_skills,
        required_skill,
    ) is expected


def test_match_required_skills():
    resume = {
        "skills": [
            "Python",
            "Azure",
            "Docker",
        ]
    }

    jd = {
        "required_skills": [
            "Python",
            "Azure",
            "Kubernetes",
        ],
        "preferred_skills": [],
    }

    result = match_skills(resume, jd)

    assert result["required_score"] == 67
    assert "Python" in result["required_matched"]
    assert "Azure" in result["required_matched"]
    assert "Kubernetes" in result["required_missing"]


def test_match_preferred_skills_separately():
    resume = {
        "skills": [
            "Python",
            "Docker",
        ]
    }

    jd = {
        "required_skills": [
            "Python",
        ],
        "preferred_skills": [
            "Docker",
            "Kubernetes",
        ],
    }

    result = match_skills(resume, jd)

    assert result["required_score"] == 100
    assert result["preferred_score"] == 50
    assert "Docker" in result["preferred_matched"]
    assert "Kubernetes" in result["preferred_missing"]


def test_no_required_skills_returns_none_score():
    resume = {
        "skills": ["Python"]
    }

    jd = {
        "required_skills": [],
        "preferred_skills": [],
    }

    result = match_skills(resume, jd)

    assert result["required_score"] is None
    assert result["preferred_score"] is None


def test_duplicate_skills_do_not_inflate_score():
    resume = {
        "skills": [
            "Python",
            "Azure",
        ]
    }

    jd = {
        "required_skills": [
            "Python",
            "Python",
            "Azure",
        ],
        "preferred_skills": [],
    }

    result = match_skills(resume, jd)

    assert result["required_score"] == 100
    assert result["required"] == [
        "Python",
        "Azure",
    ]


def test_alternative_group_is_satisfied_by_one_option():
    resume = {
        "skills": [
            "Azure",
        ]
    }

    jd = {
        "alternative_groups": [
            {
                "options": [
                    "AWS",
                    "Azure",
                    "GCP",
                ],
                "source": "Experience with AWS, Azure, or GCP.",
            }
        ]
    }

    result = match_alternative_groups(
        resume,
        jd,
    )

    assert len(result) == 1
    assert result[0]["satisfied"] is True
    assert "Azure" in result[0]["matched"]


def test_alternative_group_fails_when_no_option_matches():
    resume = {
        "skills": [
            "Docker",
        ]
    }

    jd = {
        "alternative_groups": [
            {
                "options": [
                    "AWS",
                    "Azure",
                    "GCP",
                ],
                "source": "Experience with AWS, Azure, or GCP.",
            }
        ]
    }

    result = match_alternative_groups(
        resume,
        jd,
    )

    assert len(result) == 1
    assert result[0]["satisfied"] is False
    assert result[0]["matched"] == []