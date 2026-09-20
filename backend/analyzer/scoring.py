import re

from analyzer.resume_analyzer import SKILL_ALIASES


# Canonical concept aliases used across JDs. These are general concepts, not
# company-specific rules. Unknown requirements still fall back to lexical evidence.
CONCEPT_ALIASES = {
    "incident management": ["incident management", "incident response", "incident handling"],
    "monitoring": ["monitoring", "application monitoring", "system monitoring"],
    "alerting": ["alerting", "alerts"],
    "observability": ["observability"],
    "on-call": ["on-call", "on call"],
    "log analysis": ["log analysis", "log investigation", "application logs", "logs"],
    "production troubleshooting": ["production troubleshooting", "production support", "production issues", "troubleshooting"],
    "root cause analysis": ["root cause analysis", "rca"],
    "automation": ["automation", "automated", "automate", "scripting"],
    "cloud": ["cloud", "cloud services", "cloud infrastructure", "cloud platform", "azure", "aws", "gcp"],
    "infrastructure as code": ["infrastructure as code", "iac", "terraform", "infrastructure provisioning", "infrastructure automation"],
    "software development": ["software development", "software engineering", "sdlc", "application development"],
    "data analytics": ["data analytics", "analytics", "analytical", "analysis"],
    "data science": ["data science", "machine learning", "ml"],
    "machine learning": ["machine learning", "ml"],
    "data security": ["data security", "security", "secure coding", "security compliance", "cybersecurity"],
    "data privacy": ["data protection", "privacy", "data privacy"],
    "agile": ["agile", "scrum", "sprint"],
    "project management": ["project management", "project manager", "project coordination"],
    "continuous improvement": ["continuous improvement", "optimization", "improvement"],
    "customer communication": ["customer communication", "customer-facing", "client communication", "stakeholder communication"],
    "escalation": ["escalation", "escalate"],
    "sla management": ["sla", "service level agreement", "service levels"],
    "version control": ["version control", "git", "github", "gitlab", "repository", "source code repository"],
    "containerization": ["container", "containers", "containerization", "docker", "kubernetes", "k8s", "container orchestration"],
    "networking": ["networking", "network security", "network"],
    "testing": ["testing", "test automation", "automated tests", "unit tests", "integration tests"],
    "database": ["database", "databases", "sql", "postgresql", "mysql", "oracle", "mongodb", "cosmos db"],
    "api development": ["api development", "rest api", "restful api", "web services", "fastapi", "flask"],
}

# Small lexical normalization table for common word forms. This helps generic
# requirement matching without pretending to be a semantic language model.
WORD_EQUIVALENTS = {
    "develop": {"develop", "developed", "development", "developer", "developing"},
    "deploy": {"deploy", "deployed", "deployment", "deployments", "deploying"},
    "automate": {"automate", "automated", "automation", "automating"},
    "analyze": {"analyze", "analyzed", "analysis", "analytics", "analytical"},
    "manage": {"manage", "managed", "management", "managing"},
    "secure": {"secure", "secured", "security", "securing"},
    "monitor": {"monitor", "monitored", "monitoring"},
    "configure": {"configure", "configured", "configuration", "configurations"},
    "provision": {"provision", "provisioned", "provisioning"},
    "collaborate": {"collaborate", "collaborated", "collaboration", "collaborating"},
    "integrate": {"integrate", "integrated", "integration", "integrating"},
    "test": {"test", "tests", "tested", "testing"},
}


def unique(items):
    result = []
    seen = set()
    for item in items or []:
        key = normalize(item)
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def normalize(value):
    value = str(value or "")
    value = value.replace("–", "-").replace("—", "-").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value.lower()).strip()


def percentage(matched, total):
    if total <= 0:
        return None
    return round((matched / total) * 100)


def term_in_text(text, term):
    text = normalize(text)
    term = normalize(term)
    if not term:
        return False
    escaped = re.escape(term)
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text, flags=re.IGNORECASE) is not None


def normalize_token(token):
    token = normalize(token).strip("._-/+&#")
    if len(token) > 5 and token.endswith("ies"):
        token = token[:-3] + "y"
    elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    return token


def token_variants(token):
    token = normalize_token(token)
    variants = {token}
    for canonical, forms in WORD_EQUIVALENTS.items():
        normalized_forms = {normalize_token(form) for form in forms}
        if token in normalized_forms:
            variants.update(normalized_forms)
            variants.add(canonical)
    return variants


def text_token_set(text):
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}", str(text or ""))
    result = set()
    for token in tokens:
        result.update(token_variants(token))
    return result


def build_resume_skill_set(resume):
    return {normalize(skill) for skill in resume.get("skills", []) if skill}


def canonical_skill_aliases(skill):
    aliases = SKILL_ALIASES.get(skill, [])
    return {normalize(skill), *(normalize(alias) for alias in aliases)}


def skill_matches(resume_skills, required_skill):
    target_aliases = canonical_skill_aliases(required_skill)
    if target_aliases.intersection(resume_skills):
        return True

    # Resume skills may contain a canonical name while the JD uses one alias.
    for resume_skill in resume_skills:
        for canonical, aliases in SKILL_ALIASES.items():
            canonical_set = {normalize(canonical), *(normalize(alias) for alias in aliases)}
            if resume_skill in canonical_set and target_aliases.intersection(canonical_set):
                return True
    return False


def match_skills(resume, jd):
    resume_skills = build_resume_skill_set(resume)
    required = unique(jd.get("required_skills", []))
    preferred = unique(jd.get("preferred_skills", []))

    required_matched = [skill for skill in required if skill_matches(resume_skills, skill)]
    required_missing = [skill for skill in required if skill not in required_matched]
    preferred_matched = [skill for skill in preferred if skill_matches(resume_skills, skill)]
    preferred_missing = [skill for skill in preferred if skill not in preferred_matched]

    return {
        "required": required,
        "required_matched": required_matched,
        "required_missing": required_missing,
        "required_score": percentage(len(required_matched), len(required)),
        "preferred": preferred,
        "preferred_matched": preferred_matched,
        "preferred_missing": preferred_missing,
        "preferred_score": percentage(len(preferred_matched), len(preferred)),
    }


def match_alternative_groups(resume, jd):
    resume_skills = build_resume_skill_set(resume)
    results = []

    for group in jd.get("alternative_groups", []):
        options = unique(group.get("options", []))
        matched = [option for option in options if skill_matches(resume_skills, option)]
        results.append({
            "options": options,
            "matched": matched,
            "satisfied": bool(matched),
            "source": group.get("source", ""),
        })
    return results


def general_requirement_matches(resume_text, requirement):
    aliases = CONCEPT_ALIASES.get(normalize(requirement), [requirement])
    return any(term_in_text(resume_text, alias) for alias in aliases)


def match_general_requirements(resume, resume_text, jd):
    requirements = unique(jd.get("general_requirements", []))
    matched = [item for item in requirements if general_requirement_matches(resume_text, item)]
    missing = [item for item in requirements if item not in matched]

    return {
        "required_matched": matched,
        "required_missing": missing,
        "required_score": percentage(len(matched), len(requirements)),
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
            "status": "No explicit minimum experience requirement was detected.",
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
        status = f"Meets the minimum experience requirement ({resume_years:.2f} years detected vs {required_years:.1f}+ required)."
    else:
        score = max(0, min(round((resume_years / required_years) * 100), 99))
        status = f"Below the minimum experience requirement ({resume_years:.2f} years detected vs {required_years:.1f}+ required)."

    return {
        "score": score,
        "status": status,
        "resume_years": resume_years,
        "required_years": required_years,
        "confidence": resume.get("experience_confidence", "low"),
    }


def match_roles(resume, jd):
    resume_roles = unique(resume.get("roles", []))
    jd_roles = unique(jd.get("roles", []))

    if not jd_roles:
        return {
            "score": None,
            "status": "No specific role category was confidently detected.",
            "matched_roles": [],
            "resume_roles": resume_roles,
            "jd_roles": [],
        }

    matched = [role for role in jd_roles if role in resume_roles]
    score = percentage(len(matched), len(jd_roles))
    status = (
        "Role alignment identified: " + ", ".join(matched) + "."
        if matched
        else "No direct role-category alignment was identified."
    )

    return {
        "score": score,
        "status": status,
        "matched_roles": matched,
        "resume_roles": resume_roles,
        "jd_roles": jd_roles,
    }


def lexical_requirement_score(resume_tokens, keywords):
    keywords = unique(keywords)
    if not keywords:
        return None

    matched = 0
    for keyword in keywords:
        variants = token_variants(keyword)
        if variants.intersection(resume_tokens):
            matched += 1

    return round((matched / len(keywords)) * 100)


def signal_requirement_score(resume, resume_text, item):
    resume_skills = build_resume_skill_set(resume)
    signal_results = []

    for skill in item.get("skills", []):
        signal_results.append(100 if skill_matches(resume_skills, skill) else 0)

    for requirement in item.get("general_requirements", []):
        signal_results.append(100 if general_requirement_matches(resume_text, requirement) else 0)

    resume_roles = set(resume.get("roles", []))
    for role in item.get("roles", []):
        signal_results.append(100 if role in resume_roles else 0)

    if not signal_results:
        return None
    return round(sum(signal_results) / len(signal_results))


def match_requirement_lines(resume, resume_text, jd):
    """Evaluate arbitrary JD requirement lines using known signals plus lexical evidence."""
    resume_tokens = text_token_set(resume_text)
    required_scores = []
    preferred_scores = []
    matched = []
    partial = []
    missing = []
    preferred_matched = []
    preferred_partial = []
    preferred_missing = []
    unmeasured = []
    details = []

    for item in jd.get("requirement_lines", []):
        category = item.get("category")
        requirement_type = item.get("type", "responsibility")
        line = item.get("text", "")

        # Experience and education have dedicated matching logic.
        if category in {"experience", "education"}:
            continue

        if not item.get("measurable", True) or category == "soft_skill":
            unmeasured.append(line)
            details.append({"text": line, "type": requirement_type, "score": None, "status": "not_reliably_measurable"})
            continue

        signal_score = signal_requirement_score(resume, resume_text, item)
        lexical_score = lexical_requirement_score(resume_tokens, item.get("keywords", []))

        if signal_score is not None and lexical_score is not None:
            line_score = round((signal_score * 0.70) + (lexical_score * 0.30))
        elif signal_score is not None:
            line_score = signal_score
        else:
            line_score = lexical_score

        if line_score is None:
            unmeasured.append(line)
            details.append({"text": line, "type": requirement_type, "score": None, "status": "not_reliably_measurable"})
            continue

        if requirement_type == "preferred":
            preferred_scores.append(line_score)
            if line_score >= 70:
                preferred_matched.append(line)
                status = "matched"
            elif line_score >= 35:
                preferred_partial.append(line)
                status = "partial"
            else:
                preferred_missing.append(line)
                status = "missing"
        else:
            required_scores.append(line_score)
            if line_score >= 70:
                matched.append(line)
                status = "matched"
            elif line_score >= 35:
                partial.append(line)
                status = "partial"
            else:
                missing.append(line)
                status = "missing"

        details.append({
            "text": line,
            "type": requirement_type,
            "score": line_score,
            "status": status,
            "signal_score": signal_score,
            "lexical_score": lexical_score,
        })

    measured_count = len(required_scores) + len(preferred_scores)
    total_count = measured_count + len(unmeasured)
    coverage = percentage(measured_count, total_count)

    return {
        "score": round(sum(required_scores) / len(required_scores)) if required_scores else None,
        "preferred_score": round(sum(preferred_scores) / len(preferred_scores)) if preferred_scores else None,
        "matched": matched,
        "partial": partial,
        "missing": missing,
        "preferred_matched": preferred_matched,
        "preferred_partial": preferred_partial,
        "preferred_missing": preferred_missing,
        "not_reliably_measurable": unmeasured,
        "measured_requirements": measured_count,
        "total_requirements": total_count,
        "coverage": coverage,
        "details": details,
    }


# Kept for API compatibility: keyword_match now represents generic requirement evidence.
def keyword_responsibility_match(resume_text, jd, resume=None):
    resume = resume or {"skills": [], "roles": []}
    return match_requirement_lines(resume, resume_text, jd)


def resume_degree_levels(resume, resume_text):
    education = " ".join(resume.get("education", [])) + " " + str(resume_text or "")
    normalized = normalize(education)
    levels = set()

    if re.search(r"\bmca\b|\bmba\b|\bm\.?sc\b|\bm\.?com\b|\bllm\b|\bm\.?pharm\b|\bmaster(?:'s)?\b|\bpostgraduate\b", normalized):
        levels.add("master")
    if re.search(r"\bbca\b|\bb\.?sc\b|\bb\.?com\b|\bllb\b|\bmbbs\b|\bb\.?pharm\b|\bbachelor(?:'s)?\b|\bb\.?tech\b|\bb\.e\.?\b|\bundergraduate\b", normalized):
        levels.add("bachelor")
    if re.search(r"\bdiploma\b", normalized):
        levels.add("diploma")
    if resume.get("education"):
        levels.add("generic")
    return levels


def education_match(resume, jd, resume_text=""):
    requirements = jd.get("education_requirements", [])

    # Backward-compatible fallback for older JD structures.
    if not requirements:
        legacy = unique(jd.get("education", []))
        if not legacy:
            return None
        requirements = [{"text": item, "level": "generic", "field_keywords": [], "allows_related": True} for item in legacy]

    levels = resume_degree_levels(resume, resume_text)
    resume_tokens = text_token_set(resume_text)
    scores = []

    for requirement in requirements:
        level = requirement.get("level", "generic")
        field_keywords = requirement.get("field_keywords", [])
        allows_related = requirement.get("allows_related", False)

        if level == "master":
            level_score = 100 if "master" in levels else 0
        elif level == "bachelor":
            level_score = 100 if {"bachelor", "master"}.intersection(levels) else 0
        elif level == "diploma":
            level_score = 100 if {"diploma", "bachelor", "master"}.intersection(levels) else 0
        else:
            level_score = 100 if levels else 0

        if level_score == 0:
            scores.append(0)
            continue

        if not field_keywords:
            scores.append(level_score)
            continue

        field_score = lexical_requirement_score(resume_tokens, field_keywords) or 0
        if field_score >= 50:
            scores.append(100)
        elif allows_related:
            # A related/equivalent qualification cannot be verified perfectly from
            # text alone, so keep the result positive but conservative.
            scores.append(85)
        else:
            scores.append(50)

    return round(sum(scores) / len(scores)) if scores else None


def build_skill_gap_lists(skill_result, alternative_results):
    required_missing = list(skill_result["required_missing"])
    preferred_missing = list(skill_result["preferred_missing"])
    satisfied_options = set()

    for group in alternative_results:
        if group.get("satisfied"):
            for option in group.get("options", []):
                satisfied_options.add(normalize(option))

    required_missing = [skill for skill in required_missing if normalize(skill) not in satisfied_options]
    critical_missing = list(required_missing)
    return unique(required_missing), unique(preferred_missing), unique(critical_missing)


def build_score_explanations(required_skill_score, general_score, experience_result, requirement_result, role_result, education_result, alternative_results):
    explanations = {
        "required_skills": (
            f"Matched {required_skill_score}% of explicitly detected required skills."
            if required_skill_score is not None else
            "No explicit canonical skills were detected; generic requirement evidence is used instead."
        ),
        "general_requirements": (
            f"Matched {general_score}% of recognized capability areas."
            if general_score is not None else
            "No predefined capability areas were detected."
        ),
        "experience": experience_result.get("status", "Experience could not be evaluated."),
        "keyword_responsibility": (
            f"Requirement evidence score is {requirement_result['score']}% with {requirement_result.get('coverage')}% measurable coverage."
            if requirement_result.get("score") is not None else
            "Required responsibilities could not be measured reliably from the available text."
        ),
        "role_alignment": role_result.get("status", "Role alignment could not be evaluated."),
        "education": (
            f"Education requirement match score is {education_result}%."
            if education_result is not None else
            "No education requirement was detected."
        ),
    }

    if alternative_results:
        satisfied = sum(1 for item in alternative_results if item.get("satisfied"))
        explanations["alternative_requirements"] = f"Satisfied {satisfied} of {len(alternative_results)} alternative requirement groups."
    else:
        explanations["alternative_requirements"] = "No alternative requirement groups were detected."

    return explanations


def apply_coverage_guard(score, coverage):
    """Avoid near-perfect scores when too little of the JD was measurable."""
    if coverage is None:
        return score
    if coverage < 40:
        return min(score, 70)
    if coverage < 60:
        return min(score, 80)
    if coverage < 75:
        return min(score, 90)
    return score


def calculate_jd_match(resume, resume_text, jd):
    skill_result = match_skills(resume, jd)
    alternative_results = match_alternative_groups(resume, jd)
    general_result = match_general_requirements(resume, resume_text, jd)
    experience_result = match_experience(resume, jd)
    role_result = match_roles(resume, jd)
    requirement_result = match_requirement_lines(resume, resume_text, jd)
    education_result = education_match(resume, jd, resume_text)

    missing_skills, preferred_missing_skills, critical_missing_skills = build_skill_gap_lists(
        skill_result,
        alternative_results,
    )
    matched_skills = unique(skill_result["required_matched"] + skill_result["preferred_matched"])

    required_skill_score = skill_result["required_score"]
    general_score = general_result["required_score"]
    experience_score = experience_result["score"]
    role_score = role_result["score"]
    requirement_score = requirement_result["score"]
    preferred_score = skill_result["preferred_score"]
    preferred_requirement_score = requirement_result["preferred_score"]
    alternative_score = percentage(
        sum(1 for item in alternative_results if item.get("satisfied")),
        len(alternative_results),
    )

    score_explanations = build_score_explanations(
        required_skill_score,
        general_score,
        experience_result,
        requirement_result,
        role_result,
        education_result,
        alternative_results,
    )

    components = []

    def add_component(value, weight):
        if value is not None:
            components.append((value, weight))

    # Requirement evidence is the generic backbone; explicit skills and hard
    # constraints remain important when the JD provides them.
    add_component(requirement_score, 35)
    add_component(required_skill_score, 25)
    add_component(experience_score, 20)
    add_component(education_result, 10)
    add_component(general_score, 10)
    add_component(role_score, 5)

    # Preferred/alternative requirements have smaller influence.
    add_component(preferred_score, 5)
    add_component(preferred_requirement_score, 5)
    add_component(alternative_score, 5)

    if components:
        weighted_sum = sum(value * weight for value, weight in components)
        weight_sum = sum(weight for _, weight in components)
        match_score = round(weighted_sum / weight_sum)
    else:
        match_score = 0

    match_score = apply_coverage_guard(match_score, requirement_result.get("coverage"))

    # Hard guards for clearly unmet explicit constraints.
    if experience_score is not None and experience_score < 100:
        match_score = min(match_score, 97)
    if required_skill_score is not None and required_skill_score < 50:
        match_score = min(match_score, 69)

    return {
        "match_score": match_score,
        "breakdown": {
            "required_skills": required_skill_score,
            "required_general_requirements": general_score,
            "experience": experience_score,
            "keyword_responsibility": requirement_score,
            "role_alignment": role_score,
            "preferred_requirements": preferred_score,
            "preferred_requirement_evidence": preferred_requirement_score,
            "education": education_result,
            "alternative_requirements": alternative_score,
            "requirement_coverage": requirement_result.get("coverage"),
        },
        "score_explanations": score_explanations,
        "required_skill_breakdown": {
            "total": skill_result["required"],
            "matched": skill_result["required_matched"],
            "missing": missing_skills,
            "score": required_skill_score,
        },
        "preferred_skill_breakdown": {
            "total": skill_result["preferred"],
            "matched": skill_result["preferred_matched"],
            "missing": preferred_missing_skills,
            "score": preferred_score,
        },
        "required_skills": skill_result["required_matched"],
        "preferred_skills": skill_result["preferred_matched"],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "critical_missing_skills": critical_missing_skills,
        "preferred_missing_skills": preferred_missing_skills,
        "experience_match": experience_result,
        "role_match": role_result,
        "keyword_match": requirement_score,
        "keyword_match_details": requirement_result,
        "education_match": education_result,
        "general_requirements": general_result,
        "alternative_requirements": alternative_results,
        "requirement_coverage": {
            "score": requirement_result.get("coverage"),
            "measured": requirement_result.get("measured_requirements", 0),
            "total": requirement_result.get("total_requirements", 0),
            "not_reliably_measurable": requirement_result.get("not_reliably_measurable", []),
        },
    }


# Calculate independent resume-quality dimensions before combining them.
def calculate_resume_quality(resume, ats=None, sections=None):
    ats = ats or {}
    sections = sections or {}
    existing_quality = resume.get("experience_quality", {})

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

    experience_quality = existing_quality.get("quality_score", 0)
    skills = resume.get("skills", [])
    skill_score = min(len(skills) * 1.5, 15)
    quantified_ratio = existing_quality.get("quantified_ratio", 0)
    action_ratio = existing_quality.get("action_verb_ratio", 0)
    achievement_score = min((quantified_ratio * 0.08) + (action_ratio * 0.02), 10)

    ats_score = ats.get("score")
    if ats_score is None:
        ats_score = 0

    standard_sections = ["summary", "skills", "experience", "education", "projects"]
    detected_sections = sum(1 for section in standard_sections if sections.get(section))
    structure_score = min(detected_sections * 2, 10)

    language_score = 10
    issues = ats.get("issues", [])
    if issues:
        language_score = max(0, language_score - min(len(issues), 5))

    breakdown = {
        "content_completeness": content_score,
        "experience_quality": round(experience_quality * 0.20),
        "skills": round(skill_score),
        "achievement_impact": round(achievement_score),
        "ats_compatibility": round(ats_score * 0.15),
        "structure_clarity": structure_score,
        "language_quality": language_score,
    }

    score = min(round(sum(breakdown.values())), 99)
    return {"score": score, "breakdown": breakdown}
