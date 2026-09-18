import re

SKILL_EQUIVALENTS = {
    "kql": {"kusto"},
    "kusto": {"kql"},
    "servicenow": {"service now"},
    "power bi": {"powerbi"},
    "microsoft fabric": {"ms fabric"},
    "llm": {
        "large language model",
        "large language models",
    },
    "ai": {"artificial intelligence"},
    "ml": {"machine learning"},
    "mcp": {"model context protocol"},
    "node.js": {
        "node",
        "nodejs",
    },
    "rest api": {"restful api"},
}


def unique(items):
    result = []

    for item in items or []:
        if item not in result:
            result.append(item)

    return result


def normalize(value):
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def percentage(matched, total):
    if total <= 0:
        return None

    return round((matched / total) * 100)


def term_in_text(text, term):
    text = normalize(text)
    term = normalize(term)

    if not term:
        return False

    # Use custom boundaries so technical terms such as C# and C++ match safely.
    escaped = re.escape(term)

    return (
        re.search(
            rf"(?<![a-z0-9]){escaped}(?![a-z0-9])",
            text,
            flags=re.IGNORECASE,
        )
        is not None
    )


def build_resume_skill_set(resume):
    skills = resume.get("skills", [])

    return {
        normalize(skill)
        for skill in skills
        if skill
    }


def skill_matches(resume_skills, required_skill):
    target = normalize(required_skill)

    if target in resume_skills:
        return True

    equivalents = SKILL_EQUIVALENTS.get(target, set())

    return bool(equivalents.intersection(resume_skills))


def match_skills(resume, jd):
    resume_skills = build_resume_skill_set(resume)

    required = unique(jd.get("required_skills", []))
    preferred = unique(jd.get("preferred_skills", []))

    required_matched = []
    required_missing = []

    for skill in required:
        if skill_matches(resume_skills, skill):
            required_matched.append(skill)
        else:
            required_missing.append(skill)

    preferred_matched = []
    preferred_missing = []

    for skill in preferred:
        if skill_matches(resume_skills, skill):
            preferred_matched.append(skill)
        else:
            preferred_missing.append(skill)

    return {
        "required_matched": required_matched,
        "required_missing": required_missing,
        "required_score": percentage(
            len(required_matched),
            len(required),
        ),
        "preferred_matched": preferred_matched,
        "preferred_missing": preferred_missing,
        "preferred_score": percentage(
            len(preferred_matched),
            len(preferred),
        ),
    }


def match_alternative_groups(resume, jd):
    resume_skills = build_resume_skill_set(resume)
    results = []

    for group in jd.get("alternative_groups", []):
        options = unique(group.get("options", []))

        matched = [
            option
            for option in options
            if skill_matches(resume_skills, option)
        ]

        results.append(
            {
                "options": options,
                "matched": matched,
                "satisfied": bool(matched),
                "source": group.get("source", ""),
            }
        )

    return results


def match_general_requirements(resume, resume_text, jd):
    text = normalize(resume_text)
    requirements = unique(jd.get("general_requirements", []))

    aliases = {
        "incident management": [
            "incident management",
            "incident response",
            "incident handling",
        ],
        "monitoring": [
            "monitoring",
            "monitor",
            "application monitoring",
        ],
        "alerting": [
            "alerting",
            "alerts",
        ],
        "observability": [
            "observability",
        ],
        "on-call": [
            "on-call",
            "on call",
        ],
        "log analysis": [
            "log analysis",
            "log traversal",
            "log investigation",
            "application logs",
        ],
        "production troubleshooting": [
            "production troubleshooting",
            "production support",
            "production issues",
            "troubleshooting",
        ],
        "root cause analysis": [
            "root cause analysis",
            "rca",
        ],
        "automation": [
            "automation",
            "automated",
            "automate",
        ],
        "cloud services": [
            "cloud services",
            "cloud infrastructure",
            "cloud platform",
        ],
        "continuous improvement": [
            "continuous improvement",
        ],
        "customer communication": [
            "customer communication",
            "customer-facing",
        ],
        "escalation": [
            "escalation",
            "escalate",
        ],
        "SLA management": [
            "sla",
            "service level agreement",
        ],
    }

    matched = []
    missing = []

    for requirement in requirements:
        candidates = aliases.get(requirement, [requirement])

        found = any(
            term_in_text(text, candidate)
            for candidate in candidates
        )

        if found:
            matched.append(requirement)
        else:
            missing.append(requirement)

    return {
        "required_matched": matched,
        "required_missing": missing,
        "required_score": percentage(
            len(matched),
            len(requirements),
        ),
        "preferred_matched": [],
        "preferred_missing": [],
        "preferred_score": None,
    }


def match_experience(resume, jd):
    resume_years = resume.get("experience_years")
    required_years = jd.get("required_years")

    if required_years is None:
        return {
            "score": None,
            "status": (
                "Experience requirement could not be determined "
                "from the job description."
            ),
            "resume_years": resume_years,
            "required_years": None,
            "confidence": "low",
        }

    if resume_years is None:
        return {
            "score": None,
            "status": "Resume experience could not be determined reliably.",
            "resume_years": None,
            "required_years": required_years,
            "confidence": "low",
        }

    if resume_years >= required_years:
        score = 100
        status = (
            f"Meets the minimum experience requirement "
            f"({resume_years:.2f} years detected vs "
            f"{required_years:.1f}+ required)."
        )
    else:
        score = round((resume_years / required_years) * 100)
        score = max(0, min(score, 99))
        status = (
            f"Below the minimum experience requirement "
            f"({resume_years:.2f} years detected vs "
            f"{required_years:.1f}+ required)."
        )

    return {
        "score": score,
        "status": status,
        "resume_years": resume_years,
        "required_years": required_years,
        "confidence": resume.get(
            "experience_confidence",
            "low",
        ),
    }


def match_roles(resume, jd):
    resume_roles = unique(resume.get("roles", []))
    jd_roles = unique(jd.get("roles", []))

    if not jd_roles:
        return {
            "score": None,
            "status": "No specific role requirement detected.",
            "matched_roles": [],
            "resume_roles": resume_roles,
            "jd_roles": [],
        }

    matched = [
        role
        for role in jd_roles
        if role in resume_roles
    ]

    score = percentage(
        len(matched),
        len(jd_roles),
    )

    if matched:
        status = "Role alignment identified: " + ", ".join(matched) + "."
    else:
        status = "No direct role alignment was identified."

    return {
        "score": score,
        "status": status,
        "matched_roles": matched,
        "resume_roles": resume_roles,
        "jd_roles": jd_roles,
    }


def keyword_responsibility_match(resume_text, jd):
    resume_text = normalize(resume_text)
    lines = jd.get("requirement_lines", [])

    required_lines = [
        item
        for item in lines
        if item.get("type") == "required"
    ]

    if not required_lines:
        return {
            "score": None,
            "matched": [],
            "missing": [],
        }

    matched = []
    missing = []

    for item in required_lines:
        line = item.get("text", "")

        signals = unique(
            item.get("skills", [])
            + item.get("general_requirements", [])
            + item.get("roles", [])
        )

        if not signals:
            continue

        found = any(
            term_in_text(resume_text, signal)
            for signal in signals
        )

        if found:
            matched.append(line)
        else:
            missing.append(line)

    total = len(matched + missing)

    return {
        "score": percentage(
            len(matched),
            total,
        ),
        "matched": matched,
        "missing": missing,
    }


def education_match(resume, jd):
    resume_education = {
        normalize(item)
        for item in resume.get("education", [])
    }

    required_education = unique(
        jd.get("education", [])
    )

    if not required_education:
        return None

    matched = []

    for education in required_education:
        target = normalize(education)

        if target in resume_education:
            matched.append(education)
            continue

        if (
            "bachelor" in target
            and any(
                value in resume_education
                for value in [
                    "bca",
                    "b.tech",
                    "be",
                    "bachelor's degree",
                ]
            )
        ):
            matched.append(education)
            continue

        if (
            "master" in target
            and any(
                value in resume_education
                for value in [
                    "mca",
                    "master's degree",
                ]
            )
        ):
            matched.append(education)

    return percentage(
        len(matched),
        len(required_education),
    )


def build_skill_gap_lists(skill_result, alternative_results):
    required_missing = list(
        skill_result["required_missing"]
    )
    preferred_missing = list(
        skill_result["preferred_missing"]
    )

    # Exclude options from critical gaps when an alternative group is satisfied.
    satisfied_options = set()

    for group in alternative_results:
        if group.get("satisfied"):
            for option in group.get("options", []):
                satisfied_options.add(
                    normalize(option)
                )

    required_missing = [
        skill
        for skill in required_missing
        if normalize(skill) not in satisfied_options
    ]

    critical_missing = list(required_missing)

    return (
        unique(required_missing),
        unique(preferred_missing),
        unique(critical_missing),
    )


def calculate_jd_match(resume, resume_text, jd):
    # Calculate each independent matching component.
    skill_result = match_skills(resume, jd)
    alternative_results = match_alternative_groups(
        resume,
        jd,
    )
    general_result = match_general_requirements(
        resume,
        resume_text,
        jd,
    )
    experience_result = match_experience(
        resume,
        jd,
    )
    role_result = match_roles(
        resume,
        jd,
    )
    keyword_result = keyword_responsibility_match(
        resume_text,
        jd,
    )
    education_result = education_match(
        resume,
        jd,
    )

    (
        missing_skills,
        preferred_missing_skills,
        critical_missing_skills,
    ) = build_skill_gap_lists(
        skill_result,
        alternative_results,
    )

    matched_skills = unique(
        skill_result["required_matched"]
        + skill_result["preferred_matched"]
    )

    required_skill_score = skill_result["required_score"]
    general_score = general_result["required_score"]
    experience_score = experience_result["score"]
    role_score = role_result["score"]
    keyword_score = keyword_result["score"]
    preferred_score = skill_result["preferred_score"]

    alternative_score = percentage(
        sum(
            1
            for item in alternative_results
            if item.get("satisfied")
        ),
        len(alternative_results),
    )

    # Build only the score components that are available.
    components = []

    def add_component(value, weight):
        if value is not None:
            components.append(
                (value, weight)
            )

    add_component(required_skill_score, 30)
    add_component(general_score, 20)
    add_component(experience_score, 20)
    add_component(keyword_score, 15)
    add_component(role_score, 10)

    if education_result is not None:
        add_component(
            education_result,
            5,
        )

    # Alternative requirements contribute modestly to avoid double-counting.
    if alternative_score is not None:
        add_component(
            alternative_score,
            5,
        )

    # Calculate the weighted overall JD match score.
    if components:
        weighted_sum = sum(
            value * weight
            for value, weight in components
        )
        weight_sum = sum(
            weight
            for _, weight in components
        )
        match_score = round(
            weighted_sum / weight_sum
        )
    else:
        match_score = 0

    # Prevent a perfect score when an explicit experience minimum is missed.
    if (
        experience_score is not None
        and experience_score < 100
    ):
        match_score = min(
            match_score,
            99,
        )

    return {
        "match_score": match_score,
        "breakdown": {
            "required_skills": required_skill_score,
            "required_general_requirements": general_score,
            "experience": experience_score,
            "keyword_responsibility": keyword_score,
            "role_alignment": role_score,
            "preferred_requirements": preferred_score,
            "education": education_result,
            "alternative_requirements": alternative_score,
        },
        "required_skills": skill_result[
            "required_matched"
        ],
        "preferred_skills": skill_result[
            "preferred_matched"
        ],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "critical_missing_skills": critical_missing_skills,
        "preferred_missing_skills": preferred_missing_skills,
        "experience_match": experience_result,
        "role_match": role_result,
        "keyword_match": keyword_score,
        "education_match": education_result,
        "general_requirements": general_result,
        "alternative_requirements": alternative_results,
    }


def calculate_resume_quality(
    resume,
    ats=None,
    sections=None,
):
    ats = ats or {}
    sections = sections or {}

    existing_quality = resume.get(
        "experience_quality",
        {},
    )

    # Score resume content completeness.
    content_score = 0

    if resume.get("name"):
        content_score += 2

    if resume.get("email"):
        content_score += 2

    if resume.get("phone"):
        content_score += 2

    if sections.get("summary"):
        content_score += 2

    if sections.get("skills"):
        content_score += 2

    if sections.get("experience"):
        content_score += 3

    if sections.get("education"):
        content_score += 2

    if sections.get("projects"):
        content_score += 2

    # Calculate experience, skills, achievement, and ATS contributions.
    experience_quality = existing_quality.get(
        "quality_score",
        0,
    )

    skills = resume.get("skills", [])
    skill_score = min(
        len(skills) * 1.5,
        15,
    )

    quantified_ratio = existing_quality.get(
        "quantified_ratio",
        0,
    )
    action_ratio = existing_quality.get(
        "action_verb_ratio",
        0,
    )

    achievement_score = min(
        (
            quantified_ratio * 0.08
            + action_ratio * 0.02
        ),
        10,
    )

    ats_score = ats.get("score")

    if ats_score is None:
        ats_score = 0

    # Measure how many standard resume sections were detected.
    standard_sections = [
        "summary",
        "skills",
        "experience",
        "education",
        "projects",
    ]

    detected_sections = sum(
        1
        for section in standard_sections
        if sections.get(section)
    )

    structure_score = min(
        detected_sections * 2,
        10,
    )

    # Reduce language quality when ATS issues are detected.
    language_score = 10
    issues = ats.get("issues", [])

    if issues:
        language_score = max(
            0,
            language_score
            - min(
                len(issues),
                5,
            ),
        )

    breakdown = {
        "content_completeness": content_score,
        "experience_quality": round(
            experience_quality * 0.20
        ),
        "skills": round(skill_score),
        "achievement_impact": round(
            achievement_score
        ),
        "ats_compatibility": round(
            ats_score * 0.15
        ),
        "structure_clarity": structure_score,
        "language_quality": language_score,
    }

    score = min(
        round(
            sum(breakdown.values())
        ),
        99,
    )

    return {
        "score": score,
        "breakdown": breakdown,
    }