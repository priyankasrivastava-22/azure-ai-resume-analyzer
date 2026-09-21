from analyzer.jd_analyzer import (
    analyze_jd,
    extract_experience_requirement,
)
from analyzer.resume_analyzer import analyze_resume
from analyzer.scoring import calculate_jd_match


def run_case(name, resume_text, sections, jd_text, minimum_score=60):
    resume = analyze_resume(resume_text, sections)
    jd = analyze_jd(jd_text)
    result = calculate_jd_match(resume, resume_text, jd)

    assert result["match_score"] >= minimum_score, (
        f"{name}: expected score >= {minimum_score}, "
        f"got {result['match_score']}"
    )

    assert result["keyword_match_details"]["total_requirements"] > 0

    return result


def test_experience_range_regression():
    assert extract_experience_requirement(
        "Should have minimum 3-4 years of professional experience."
    ) == 3.0

    assert extract_experience_requirement(
        "1-3 years of experience"
    ) == 1.0

    assert extract_experience_requirement(
        "2–4 years of relevant experience"
    ) == 2.0

    assert extract_experience_requirement(
        "3 to 5 years of experience"
    ) == 3.0


def test_devops_domain_regression():
    resume_text = """
    DEVOPS ENGINEER
    Azure Terraform Jenkins Docker Git Python Bash CI/CD infrastructure provisioning.
    Built deployment pipelines and automated cloud infrastructure.
    August 2022 - June 2025
    Bachelor of Computer Applications.
    """

    result = run_case(
        "DevOps",
        resume_text,
        {
            "skills": (
                "Azure, Terraform, Jenkins, Docker, "
                "Git, Python, Bash, CI/CD"
            ),
            "experience": (
                "DevOps Engineer | August 2022 - June 2025\n"
                "• Built deployment pipelines and automated cloud infrastructure."
            ),
            "education": "Bachelor of Computer Applications",
        },
        """
        DevOps Engineer

        Requirements
        - 1-3 years of DevOps experience.
        - Experience with Azure, Terraform, CI/CD, Git and Docker.
        - Scripting knowledge in Bash or Python.
        - Bachelor's degree in Computer Science or related field.
        """,
        70,
    )

    assert result["match_score"] >= 70


def test_finance_domain_regression():
    resume_text = """
    ACCOUNTANT
    Financial Reporting, General Ledger, Account Reconciliation,
    Microsoft Excel, SAP, Tax Compliance.
    Prepared monthly financial statements and reconciled general ledger accounts.
    January 2022 - Present
    Bachelor of Commerce in Accounting.
    """

    result = run_case(
        "Finance",
        resume_text,
        {
            "skills": (
                "Financial Reporting, General Ledger, "
                "Account Reconciliation, Microsoft Excel, "
                "SAP, Tax Compliance"
            ),
            "experience": (
                "Accountant | January 2022 - Present\n"
                "• Prepared monthly financial statements and "
                "reconciled general ledger accounts."
            ),
            "education": "Bachelor of Commerce in Accounting",
        },
        """
        Accountant

        Responsibilities
        - Prepare monthly financial statements and reconcile general ledger accounts.
        - Support tax compliance and external audits.

        Qualifications
        - Bachelor's degree in Accounting or related field.
        - Minimum 3 years of accounting experience.
        - Strong Microsoft Excel and SAP skills.
        """,
        65,
    )

    assert result["match_score"] >= 65


def test_hr_domain_regression():
    resume_text = """
    HR EXECUTIVE
    Talent Acquisition, Recruitment, Employee Relations,
    Onboarding, HRIS, Workday, Performance Management.
    Managed recruitment, onboarding, employee relations
    and employee records in Workday.
    June 2021 - Present
    Master of Business Administration in Human Resources.
    """

    result = run_case(
        "HR",
        resume_text,
        {
            "skills": (
                "Talent Acquisition, Recruitment, Employee Relations, "
                "Onboarding, HRIS, Workday, Performance Management"
            ),
            "experience": (
                "HR Executive | June 2021 - Present\n"
                "• Managed recruitment, onboarding, employee relations "
                "and Workday records."
            ),
            "education": "MBA in Human Resources",
        },
        """
        HR Generalist

        Responsibilities
        - Manage recruitment, onboarding, employee relations
          and performance management.
        - Maintain HRIS records and partner with hiring managers.

        Qualifications
        - 3+ years of HR experience.
        - Experience with Workday or similar HRIS platforms.
        - MBA in Human Resources preferred.
        """,
        60,
    )

    assert result["match_score"] >= 60


def test_nursing_domain_regression():
    resume_text = """
    STAFF NURSE
    Patient Care, Medication Administration,
    Clinical Documentation, Infection Control,
    Electronic Health Records.
    Delivered patient care, administered medication
    and maintained clinical documentation.
    July 2020 - Present
    Bachelor of Science in Nursing.
    """

    result = run_case(
        "Nursing",
        resume_text,
        {
            "skills": (
                "Patient Care, Medication Administration, "
                "Clinical Documentation, Infection Control, "
                "Electronic Health Records"
            ),
            "experience": (
                "Staff Nurse | July 2020 - Present\n"
                "• Delivered patient care and medication administration.\n"
                "• Maintained clinical documentation and infection "
                "control procedures."
            ),
            "education": "Bachelor of Science in Nursing",
        },
        """
        Staff Nurse

        Responsibilities
        - Provide direct patient care and medication administration.
        - Maintain clinical documentation and infection control procedures.

        Requirements
        - Bachelor's degree in Nursing.
        - Minimum 2 years of nursing experience.
        - Experience with electronic health records.
        """,
        60,
    )

    assert result["match_score"] >= 60


def test_alternative_requirement_parsing():
    jd = analyze_jd(
        """
        Required Skills
        - Experience with AWS, Azure, or GCP.
        - Scripting in Bash or Python.
        """
    )

    assert len(jd["alternative_groups"]) == 2


def test_satisfied_alternatives_do_not_create_false_critical_gaps():
    resume_text = """
    CLOUD ENGINEER

    SKILLS
    Azure
    Python
    """

    resume = analyze_resume(
        resume_text,
        {
            "skills": "Azure, Python",
        },
    )

    jd = analyze_jd(
        """
        Cloud Engineer

        Requirements
        - Experience with AWS, Azure, or GCP.
        - Scripting in Bash or Python.
        """
    )

    result = calculate_jd_match(
        resume,
        resume_text,
        jd,
    )

    alternatives = result["alternative_requirements"]

    assert len(alternatives) == 2

    assert all(
        item["satisfied"]
        for item in alternatives
    )

    critical_missing = {
        skill.lower()
        for skill in result["critical_missing_skills"]
    }

    assert "aws" not in critical_missing
    assert "gcp" not in critical_missing
    assert "bash" not in critical_missing


def test_soft_skill_measurability_guard():
    jd = analyze_jd(
        """
        Qualifications
        - Excellent communication skills.
        - Strong problem-solving skills.
        """
    )

    assert jd["requirement_lines"]

    assert all(
        not item["measurable"]
        for item in jd["requirement_lines"]
    )


def test_unknown_domain_returns_structured_result():
    resume_text = """
    MUSEUM COLLECTIONS ASSISTANT

    SKILLS
    Artifact Cataloging
    Collection Documentation
    Inventory Management

    EXPERIENCE
    Cataloged historical artifacts and maintained collection inventory records.
    """

    resume = analyze_resume(
        resume_text,
        {
            "skills": (
                "Artifact Cataloging, "
                "Collection Documentation, "
                "Inventory Management"
            ),
            "experience": (
                "Cataloged historical artifacts and maintained "
                "collection inventory records."
            ),
        },
    )

    jd = analyze_jd(
        """
        Museum Collections Coordinator

        Responsibilities
        - Catalog historical artifacts.
        - Maintain collection documentation.
        - Manage museum inventory records.

        Requirements
        - Experience working with museum collections and artifact records.
        """
    )

    result = calculate_jd_match(
        resume,
        resume_text,
        jd,
    )

    assert isinstance(result, dict)
    assert "match_score" in result
    assert "breakdown" in result
    assert "keyword_match_details" in result

    assert (
        result["keyword_match_details"]["total_requirements"]
        > 0
    )


def test_missing_resume_experience_does_not_claim_match():
    resume_text = """
    SOFTWARE ENGINEER

    SKILLS
    Python
    Azure
    Git
    """

    resume = analyze_resume(
        resume_text,
        {
            "skills": "Python, Azure, Git",
        },
    )

    jd = analyze_jd(
        """
        Software Engineer

        Requirements
        - Minimum 5 years of professional experience.
        - Experience with Python, Azure and Git.
        """
    )

    result = calculate_jd_match(
        resume,
        resume_text,
        jd,
    )

    experience = result["experience_match"]

    assert experience["required_years"] == 5.0
    assert experience["resume_years"] is None
    assert experience["score"] is None

    assert (
        "could not" in experience["status"].lower()
        or "not be determined" in experience["status"].lower()
    )