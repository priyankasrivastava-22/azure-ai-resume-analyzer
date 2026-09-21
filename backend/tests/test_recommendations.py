from analyzer.recommendations import (
    generate_jd_recommendations,
    generate_resume_recommendations,
)


def test_resume_recommendations_returns_lists():
    resume = {
        "name": "Priya Sharma",
        "email": "priya@example.com",
        "phone": "+91 98765 43210",
        "skills": ["Python", "Azure"],
        "experience_quality": {
            "quality_score": 70,
            "quantified_ratio": 20,
        },
    }

    quality_breakdown = {
        "content_completeness": 15,
        "experience_quality": 14,
        "skills": 10,
        "achievement_impact": 5,
        "ats_compatibility": 12,
        "structure_clarity": 8,
        "language_quality": 10,
    }

    ats = {
        "score": 80,
        "issues": [],
    }

    strengths, recommendations = generate_resume_recommendations(
        resume,
        75,
        quality_breakdown,
        ats,
    )

    assert isinstance(strengths, list)
    assert isinstance(recommendations, list)


def test_jd_recommendations_handles_none_role_score():
    resume = {
        "experience_years": 2.92,
    }

    jd = {
        "required_years": 3.0,
    }

    jd_match = {
        "critical_missing_skills": [],
        "preferred_missing_skills": [],
        "role_match": {
            "score": None,
        },
        "keyword_match": None,
        "experience_match": {
            "required_years": 3.0,
            "resume_years": 2.92,
            "score": 0,
        },
        "general_requirements": {
            "missing": [],
        },
    }

    result = generate_jd_recommendations(
        resume,
        jd,
        jd_match,
    )

    assert isinstance(result, list)


def test_recommendations_do_not_claim_unknown_skill_as_fact():
    resume = {
        "experience_years": 3.0,
    }

    jd = {
        "required_years": None,
    }

    jd_match = {
        "critical_missing_skills": ["Kubernetes"],
        "preferred_missing_skills": [],
        "role_match": {
            "score": None,
        },
        "keyword_match": None,
        "experience_match": {
            "required_years": None,
            "resume_years": 3.0,
            "score": None,
        },
        "general_requirements": {
            "missing": [],
        },
    }

    result = generate_jd_recommendations(
        resume,
        jd,
        jd_match,
    )

    combined = " ".join(result).lower()

    assert "kubernetes" in combined
    assert ("not clearly evidenced" in combined or "highlight" in combined or "genuinely have the experience" in combined)