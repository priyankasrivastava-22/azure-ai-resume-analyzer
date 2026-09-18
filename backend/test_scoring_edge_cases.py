from analyzer.scoring import calculate_jd_match


# Run one scoring test and print the important result fields.
def run_test(name, resume, resume_text, jd):
    result = calculate_jd_match(resume, resume_text, jd)
    print(f"\n{name}")
    print("Match score:", result["match_score"])
    print("Required skills:", result["required_skill_breakdown"])
    print("Experience:", result["experience_match"])
    print("Keyword match:", result["keyword_match"])


# Test an almost empty resume.
run_test(
    "TEST 1 - Empty resume",
    {"skills": [], "roles": [], "education": []},
    "",
    {
        "required_skills": ["Docker", "Linux"],
        "preferred_skills": [],
        "alternative_groups": [],
        "general_requirements": [],
        "required_years": 2,
        "roles": [],
        "requirement_lines": [],
        "education": [],
    },
)


# Test a JD with no measurable requirements.
run_test(
    "TEST 2 - Empty JD requirements",
    {"skills": ["Docker"], "roles": [], "education": []},
    "Docker",
    {
        "required_skills": [],
        "preferred_skills": [],
        "alternative_groups": [],
        "general_requirements": [],
        "required_years": None,
        "roles": [],
        "requirement_lines": [],
        "education": [],
    },
)


# Test partial required-skill matching.
run_test(
    "TEST 3 - Partial skill match",
    {"skills": ["Docker", "Linux"], "roles": [], "education": []},
    "Docker Linux",
    {
        "required_skills": ["Docker", "Linux", "Kubernetes", "Azure"],
        "preferred_skills": [],
        "alternative_groups": [],
        "general_requirements": [],
        "required_years": None,
        "roles": [],
        "requirement_lines": [],
        "education": [],
    },
)


# Test a satisfied alternative requirement.
run_test(
    "TEST 4 - Alternative requirement",
    {"skills": ["Azure"], "roles": [], "education": []},
    "Azure",
    {
        "required_skills": ["AWS", "Azure"],
        "preferred_skills": [],
        "alternative_groups": [{"options": ["AWS", "Azure"], "source": "AWS or Azure"}],
        "general_requirements": [],
        "required_years": None,
        "roles": [],
        "requirement_lines": [],
        "education": [],
    },
)


# Test an unmet experience requirement.
run_test(
    "TEST 5 - Experience gap",
    {"skills": ["Docker"], "experience_years": 1, "roles": [], "education": []},
    "Docker",
    {
        "required_skills": ["Docker"],
        "preferred_skills": [],
        "alternative_groups": [],
        "general_requirements": [],
        "required_years": 3,
        "roles": [],
        "requirement_lines": [],
        "education": [],
    },
)


# Test partial responsibility coverage.
run_test(
    "TEST 6 - Partial responsibility coverage",
    {"skills": ["Docker"], "roles": [], "education": []},
    "Docker",
    {
        "required_skills": ["Docker", "Kubernetes", "Linux"],
        "preferred_skills": [],
        "alternative_groups": [],
        "general_requirements": [],
        "required_years": None,
        "roles": [],
        "requirement_lines": [
            {
                "type": "required",
                "text": "Experience with Docker, Kubernetes, and Linux",
                "skills": ["Docker", "Kubernetes", "Linux"],
                "general_requirements": [],
                "roles": [],
            }
        ],
        "education": [],
    },
)