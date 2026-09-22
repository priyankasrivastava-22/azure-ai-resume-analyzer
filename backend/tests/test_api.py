import json
from unittest.mock import patch

import azure.functions as func

import function_app


def make_json_request(body):
    return func.HttpRequest(
        method="POST",
        url="/api/analyze",
        headers={
            "content-type": "application/json",
        },
        params={},
        body=json.dumps(body).encode("utf-8"),
    )


def test_health_endpoint():
    request = func.HttpRequest(
        method="GET",
        url="/api/health",
        headers={},
        params={},
        body=b"",
    )

    response = function_app.health(request)
    data = json.loads(
        response.get_body().decode("utf-8")
    )

    assert response.status_code == 200
    assert data["success"] is True
    assert data["service"] == "AI Resume Analyzer"
    assert data["status"] == "healthy"


def test_analyze_rejects_empty_resume():
    request = make_json_request(
        {
            "filename": "resume.txt",
            "resume_text": "",
            "job_description": (
                "This is a complete job description "
                "with enough text to pass the minimum "
                "job description length validation."
            ),
        }
    )

    response = function_app.analyze(request)

    assert response.status_code == 400


def test_analyze_rejects_missing_job_description():
    request = make_json_request(
        {
            "filename": "resume.txt",
            "resume_text": (
                "Software Engineer with Python, "
                "Azure and automation experience."
            ),
            "job_description": "",
        }
    )

    response = function_app.analyze(request)

    assert response.status_code == 400


def test_analyze_rejects_short_job_description():
    request = make_json_request(
        {
            "filename": "resume.txt",
            "resume_text": (
                "Software Engineer with Python "
                "and Azure experience."
            ),
            "job_description": "Python developer needed.",
        }
    )

    response = function_app.analyze(request)

    assert response.status_code == 400


def test_analyze_success_response_structure():
    resume_text = """
    PRIYA SHARMA
    priya@example.com
    +91 98765 43210

    SUMMARY
    DevOps Engineer with Azure and Python experience.

    SKILLS
    Azure
    Python
    Docker
    Git

    EXPERIENCE
    Software Engineer
    January 2022 - January 2025
    - Automated deployment workflows using Python and Azure.

    EDUCATION
    Bachelor of Computer Applications
    """

    job_description = """
    We are hiring a DevOps Engineer with experience
    in Azure, Python, Git, cloud infrastructure,
    deployment automation, and troubleshooting.

    Candidates should have at least 2 years of
    professional experience working with software
    delivery and cloud environments.

    A bachelor's degree or comparable qualification
    is preferred.
    """

    request = make_json_request(
        {
            "filename": "resume.txt",
            "resume_text": resume_text,
            "job_description": job_description,
        }
    )

    fake_azure_result = {
        "key_phrases": [],
        "entities": [],
    }

    with patch(
        "function_app.analyze_text_with_azure",
        return_value=fake_azure_result,
    ):
        response = function_app.analyze(request)

    assert response.status_code == 200

    data = json.loads(
        response.get_body().decode("utf-8")
    )

    assert data["success"] is True
    assert "candidate" in data
    assert "analysis" in data
    assert "job_match" in data
    assert "azure_ai" in data

    assert "resume_score" in data["analysis"]
    assert "ats" in data["analysis"]
    assert "match_score" in data["job_match"]


def test_successful_api_does_not_require_live_azure():
    resume_text = """
    DEVOPS ENGINEER

    SKILLS
    Azure
    Python
    Docker

    EXPERIENCE
    January 2022 - January 2025
    - Automated cloud deployments.
    """

    job_description = """
    The role requires experience with Azure,
    Python, Docker, deployment automation,
    cloud platforms, and troubleshooting.
    Candidates should have at least 2 years
    of relevant professional experience.
    """

    request = make_json_request(
        {
            "filename": "resume.txt",
            "resume_text": resume_text,
            "job_description": job_description,
        }
    )

    with patch(
        "function_app.analyze_text_with_azure",
        return_value={
            "key_phrases": [],
            "entities": [],
        },
    ):
        response = function_app.analyze(request)

    assert response.status_code == 200


def test_validation_error_response_is_structured():
    request = make_json_request(
        {
            "filename": "resume.txt",
            "resume_text": "Python developer with Azure experience.",
            "job_description": "too short",
        }
    )

    response = function_app.analyze(request)
    body = json.loads(response.get_body().decode("utf-8"))

    assert response.status_code == 400
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["message"], str)
    assert body["error"]["message"]


def test_internal_error_returns_safe_generic_message(monkeypatch):
    valid_resume = """
    PRIYA SHARMA

    Email: priya@example.com
    Phone: +91 9876543210

    SUMMARY
    Software Engineer with Python, Azure, Docker, Git and CI/CD experience.

    SKILLS
    Python, Azure, Docker, Git, SQL

    EXPERIENCE
    Software Engineer with three years of development experience.

    EDUCATION
    Bachelor of Computer Applications
    """

    valid_jd = (
        "We are looking for a Software Engineer with Python, Azure, Docker, "
        "Git, SQL, CI/CD, troubleshooting, application development, testing, "
        "deployment, monitoring and software engineering experience."
    )

    request = make_json_request(
        {
            "filename": "resume.txt",
            "resume_text": valid_resume,
            "job_description": valid_jd,
        }
    )

    def raise_internal_error(*args, **kwargs):
        raise RuntimeError(
            "INTERNAL_SECRET_DETAIL_SHOULD_NEVER_REACH_CLIENT"
        )

    monkeypatch.setattr(
        function_app,
        "analyze_resume",
        raise_internal_error,
    )

    response = function_app.analyze(request)
    body = json.loads(response.get_body().decode("utf-8"))

    assert response.status_code == 500
    assert body["success"] is False
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == "Resume analysis failed."

    response_text = response.get_body().decode("utf-8")

    assert "INTERNAL_SECRET_DETAIL_SHOULD_NEVER_REACH_CLIENT" not in response_text
    assert "RuntimeError" not in response_text
