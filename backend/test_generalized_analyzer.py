from analyzer.jd_analyzer import analyze_jd, extract_experience_requirement
from analyzer.resume_analyzer import analyze_resume
from analyzer.scoring import calculate_jd_match


def run_case(name, resume_text, sections, jd_text, minimum_score=60):
    resume = analyze_resume(resume_text, sections)
    jd = analyze_jd(jd_text)
    result = calculate_jd_match(resume, resume_text, jd)

    assert result["match_score"] >= minimum_score, (
        f"{name}: expected score >= {minimum_score}, got {result['match_score']}"
    )
    assert result["keyword_match_details"]["total_requirements"] > 0
    print(
        f"PASS {name}: score={result['match_score']}, "
        f"coverage={result['keyword_match_details']['coverage']}%"
    )


def main():
    assert extract_experience_requirement(
        "Should have minimum 3-4 years of professional experience."
    ) == 3.0
    assert extract_experience_requirement("1-3 years of experience") == 1.0
    print("PASS experience-range parsing")

    devops_resume = """
    DEVOPS ENGINEER
    Azure Terraform Jenkins Docker Git Python Bash CI/CD infrastructure provisioning.
    Built deployment pipelines and automated cloud infrastructure.
    August 2022 - June 2025
    Bachelor of Computer Applications.
    """
    run_case(
        "DevOps",
        devops_resume,
        {
            "skills": "Azure, Terraform, Jenkins, Docker, Git, Python, Bash, CI/CD",
            "experience": "DevOps Engineer | August 2022 - June 2025\n• Built deployment pipelines and automated cloud infrastructure.",
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

    finance_resume = """
    ACCOUNTANT
    Financial Reporting, General Ledger, Account Reconciliation, Microsoft Excel, SAP, Tax Compliance.
    Prepared monthly financial statements and reconciled general ledger accounts.
    January 2022 - Present
    Bachelor of Commerce in Accounting.
    """
    run_case(
        "Finance",
        finance_resume,
        {
            "skills": "Financial Reporting, General Ledger, Account Reconciliation, Microsoft Excel, SAP, Tax Compliance",
            "experience": "Accountant | January 2022 - Present\n• Prepared monthly financial statements and reconciled general ledger accounts.",
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

    hr_resume = """
    HR EXECUTIVE
    Talent Acquisition, Recruitment, Employee Relations, Onboarding, HRIS, Workday, Performance Management.
    Managed recruitment, onboarding, employee relations and employee records in Workday.
    June 2021 - Present
    Master of Business Administration in Human Resources.
    """
    run_case(
        "HR",
        hr_resume,
        {
            "skills": "Talent Acquisition, Recruitment, Employee Relations, Onboarding, HRIS, Workday, Performance Management",
            "experience": "HR Executive | June 2021 - Present\n• Managed recruitment, onboarding, employee relations and Workday records.",
            "education": "MBA in Human Resources",
        },
        """
        HR Generalist
        Responsibilities
        - Manage recruitment, onboarding, employee relations and performance management.
        - Maintain HRIS records and partner with hiring managers.
        Qualifications
        - 3+ years of HR experience.
        - Experience with Workday or similar HRIS platforms.
        - MBA in Human Resources preferred.
        """,
        60,
    )

    nursing_resume = """
    STAFF NURSE
    Patient Care, Medication Administration, Clinical Documentation, Infection Control, Electronic Health Records.
    Delivered patient care, administered medication and maintained clinical documentation.
    July 2020 - Present
    Bachelor of Science in Nursing.
    """
    run_case(
        "Nursing",
        nursing_resume,
        {
            "skills": "Patient Care, Medication Administration, Clinical Documentation, Infection Control, Electronic Health Records",
            "experience": "Staff Nurse | July 2020 - Present\n• Delivered patient care and medication administration.\n• Maintained clinical documentation and infection control procedures.",
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

    jd = analyze_jd(
        "Required Skills\n- Experience with AWS, Azure, or GCP.\n- Scripting in Bash or Python."
    )
    assert len(jd["alternative_groups"]) == 2
    print("PASS alternative-requirement parsing")

    soft_jd = analyze_jd(
        "Qualifications\n- Excellent communication skills.\n- Strong problem-solving skills."
    )
    assert all(not item["measurable"] for item in soft_jd["requirement_lines"])
    print("PASS soft-skill measurability guard")

    print("\nAll generalized analyzer smoke tests passed.")


if __name__ == "__main__":
    main()
