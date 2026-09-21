from analyzer.resume_analyzer import (
    analyze_resume,
    extract_email,
    extract_explicit_skill_terms,
    extract_phone,
)


def test_extract_email():
    text = "Candidate Email: candidate@example.com"
    assert extract_email(text) == "candidate@example.com"


def test_extract_phone():
    text = "Phone: +91 98765 43210"
    result = extract_phone(text)
    assert result is not None
    assert "98765" in result


def test_extract_dynamic_skill_terms():
    text = """
    Financial Reporting
    General Ledger
    Account Reconciliation
    SAP
    Tax Compliance
    """

    result = extract_explicit_skill_terms(text)

    assert result
    assert any("financial" in item.lower() for item in result)


def test_analyze_resume_returns_standard_structure():
    text = """
    PRIYA SHARMA
    priya@example.com
    +91 98765 43210

    SUMMARY
    DevOps Engineer with experience in Azure and automation.

    SKILLS
    Azure
    Python
    Terraform
    Docker

    EXPERIENCE
    Software Engineer
    January 2022 - January 2025
    - Automated deployment pipelines using Python and Terraform.

    EDUCATION
    Bachelor of Computer Applications
    """

    sections = {
        "summary": "DevOps Engineer with experience in Azure and automation.",
        "skills": "Azure\nPython\nTerraform\nDocker",
        "experience": (
            "Software Engineer\n"
            "January 2022 - January 2025\n"
            "- Automated deployment pipelines using Python and Terraform."
        ),
        "education": "Bachelor of Computer Applications",
    }

    result = analyze_resume(text, sections)

    assert isinstance(result, dict)
    assert "skills" in result
    assert "experience_years" in result
    assert "education" in result
    assert "roles" in result
    assert "experience_quality" in result
    assert "Azure" in result["skills"]
    assert "Python" in result["skills"]


def test_resume_analyzer_supports_non_it_skills():
    text = """
    ANITA SHARMA

    SKILLS
    Talent Acquisition
    Employee Relations
    Onboarding
    Performance Management
    """

    sections = {
        "skills": (
            "Talent Acquisition\n"
            "Employee Relations\n"
            "Onboarding\n"
            "Performance Management"
        )
    }

    result = analyze_resume(text, sections)

    detected = [skill.lower() for skill in result["skills"]]

    assert any("talent acquisition" in skill for skill in detected)
    assert any("employee relations" in skill for skill in detected)