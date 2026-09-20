import re
from typing import Dict, List, Optional

from analyzer.resume_analyzer import SKILL_ALIASES, term_in_text as resume_term_in_text


# Role patterns are only used when the JD states a recognizable engineering role.
# Unknown roles are left unscored rather than forced into the wrong category.
ROLE_PATTERNS = {
    "SRE": [r"\bsite reliability engineer(?:ing)?\b", r"\bsite reliability\b", r"\bsre\b"],
    "Software Engineer": [r"\bsoftware engineer(?:ing)?\b", r"\bsoftware developer\b"],
    "DevOps Engineer": [r"\bdevops engineer(?:ing)?\b"],
    "Platform Engineer": [r"\bplatform engineer(?:ing)?\b", r"\bplatform engineering\b"],
    "Cloud Engineer": [r"\bcloud engineer(?:ing)?\b"],
    "Backend Engineer": [r"\bbackend engineer(?:ing)?\b", r"\bback[- ]end engineer(?:ing)?\b"],
    "Automation Engineer": [r"\bautomation engineer(?:ing)?\b"],
    "Data Engineer": [r"\bdata engineer(?:ing)?\b"],
    "Data Analyst": [r"\bdata analysts?\b"],
    "Data Scientist": [r"\bdata scientists?\b"],
    "Security Engineer": [r"\bsecurity engineer(?:ing)?\b", r"\bcybersecurity engineer(?:ing)?\b"],
}


# Cross-domain concepts help normalize common capability wording. They are not tied
# to one company or one JD; unknown concepts are still handled by lexical evidence.
GENERAL_PATTERNS = {
    "incident management": [r"\bincident management\b", r"\bincident response\b", r"\bincident handling\b"],
    "monitoring": [r"\bmonitoring\b", r"\bapplication monitoring\b"],
    "alerting": [r"\balerting\b", r"\balerts?\b"],
    "observability": [r"\bobservability\b"],
    "on-call": [r"\bon[- ]call\b"],
    "log analysis": [r"\blog analysis\b", r"\blog investigation\b", r"\bapplication logs?\b"],
    "production troubleshooting": [r"\bproduction troubleshooting\b", r"\bproduction support\b", r"\bproduction issues?\b"],
    "root cause analysis": [r"\broot cause analysis\b", r"\brca\b"],
    "automation": [r"\bautomation\b", r"\bautomated\b", r"\bautomate\b"],
    "cloud": [r"\bcloud services?\b", r"\bcloud infrastructure\b", r"\bcloud platforms?\b", r"\bcloud\b"],
    "infrastructure as code": [r"\binfrastructure(?:\s+|-)+as(?:\s+|-)+code\b", r"\biac\b"],
    "software development": [r"\bsoftware development\b", r"\bsoftware engineering\b", r"\bsdlc\b"],
    "data analytics": [r"\bdata analytics\b", r"\banalytical solutions?\b", r"\banalytics\b"],
    "data science": [r"\bdata science\b"],
    "machine learning": [r"\bmachine learning\b", r"\bml\b"],
    "data security": [r"\bdata security\b", r"\bsecure coding\b", r"\bsecurity compliance\b"],
    "data privacy": [r"\bdata protection\b", r"\bprivacy polic(?:y|ies)\b", r"\bdata privacy\b"],
    "agile": [r"\bagile\b", r"\bscrum\b"],
    "project management": [r"\bproject management\b", r"\bproject managers?\b"],
    "continuous improvement": [r"\bcontinuous improvement\b"],
    "customer communication": [r"\bcustomer communication\b", r"\bcustomer-facing\b"],
    "escalation": [r"\bescalation\b", r"\bescalate\b"],
    "SLA management": [r"\bslas?\b", r"\bservice level agreements?\b"],
    "version control": [r"\bversion control\b", r"\bsource code repositories?\b"],
    "containerization": [r"\bcontainers?\b", r"\bcontainerization\b", r"\bcontainer orchestration\b"],
    "networking": [r"\bnetworking\b", r"\bnetwork security\b"],
    "testing": [r"\btesting\b", r"\btest automation\b", r"\bautomated tests?\b"],
    "database": [r"\bdatabases?\b", r"\bdatabase management\b"],
    "api development": [r"\bapi development\b", r"\brest(?:ful)? apis?\b", r"\bweb services?\b"],
}


EDUCATION_PATTERNS = {
    "BCA": [r"\bbca\b", r"\bbachelor(?:'s)?\s+of\s+computer\s+applications?\b"],
    "MCA": [r"\bmca\b", r"\bmaster(?:'s)?\s+of\s+computer\s+applications?\b"],
    "B.Tech": [r"\bb\.?\s*tech\b", r"\bbachelor(?:'s)?\s+of\s+technology\b"],
    "BE": [r"\bb\.e\.?\b", r"\bbachelor(?:'s)?\s+of\s+engineering\b"],
    "Bachelor's degree": [r"\bbachelor(?:'s)?\s+degree\b", r"\bundergraduate degree\b"],
    "Master's degree": [r"\bmaster(?:'s)?\s+degree\b", r"\bpostgraduate degree\b"],
}


SECTION_HEADINGS = {
    "preferred": {
        "preferred", "preferred qualifications", "preferred skills", "preferred experience",
        "preferred requirements", "nice to have", "good to have", "bonus", "desirable",
    },
    "required": {
        "requirements", "required qualifications", "minimum qualifications", "qualifications",
        "required skills", "must have", "what you need", "your qualification", "your qualifications",
        "skills and qualifications", "experience and qualifications",
    },
    "responsibility": {
        "responsibilities", "key responsibilities", "job responsibilities", "duties",
        "your tasks", "what you'll do", "what you will do", "role responsibilities",
        "responsibilities include", "day to day", "day-to-day",
    },
    "ignore": {
        "about the job", "about us", "about the company", "benefits", "company", "location",
        "work area", "employment type", "working model", "country/region", "country region",
    },
}


PREFERRED_MARKERS = (
    "preferred", "nice to have", "nice-to-have", "good to have", "bonus", "desired",
    "desirable", "advantage", "plus", "would be beneficial", "would be a plus",
)

REQUIRED_MARKERS = (
    "required", "must", "mandatory", "minimum", "at least", "should have", "need to have",
    "essential", "strong experience", "hands-on experience", "proficiency", "expertise",
)

SOFT_SKILL_PATTERNS = (
    r"\bcommunication skills?\b", r"\bproblem[- ]solving\b", r"\bteam player\b",
    r"\binterpersonal skills?\b", r"\bleadership skills?\b", r"\btime management\b",
    r"\bindependent(?:ly)?\b", r"\bself[- ]starter\b", r"\battention to detail\b",
    r"\bmanage several topics\b", r"\bmultitask(?:ing)?\b", r"\benthusiasm\b",
)

METADATA_PREFIXES = (
    "country", "country/region", "job location", "location", "working model", "employment type",
    "company", "org unit", "requisition id", "job id", "reference id", "work area",
)

# Words that carry little matching value when evaluating a requirement sentence.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by", "for", "from", "have",
    "has", "having", "in", "into", "is", "it", "its", "of", "on", "or", "our", "the", "their",
    "to", "with", "will", "you", "your", "we", "they", "this", "that", "these", "those", "using",
    "use", "used", "work", "working", "experience", "experienced", "knowledge", "skills", "skill",
    "ability", "strong", "excellent", "good", "current", "relevant", "professional", "minimum",
    "required", "preferred", "support", "responsible", "including", "such", "within", "across",
    "field", "methods", "method", "tools", "tool", "solutions", "solution", "environment", "environments",
    "successfully", "completed", "complete", "qualification", "qualifications",
}


def normalize_text(text: str) -> str:
    text = str(text or "")
    text = (
        text.replace("â€“", "-")
        .replace("â€”", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("\u00a0", " ")
    )
    text = re.sub(r"\s+", " ", text.lower())
    return text.strip()


def clean_line(line: str) -> str:
    line = str(line or "").strip()
    line = re.sub(r"^[\s•●▪◦*\-–—]+", "", line)
    line = re.sub(r"^#{1,6}\s*", "", line)
    line = line.replace("**", "").replace("__", "").strip()
    return re.sub(r"\s+", " ", line)


def normalize_heading(line: str) -> str:
    value = clean_line(line).strip().rstrip(":")
    return normalize_text(value)


def unique(items):
    result = []
    seen = set()
    for item in items or []:
        key = normalize_text(item)
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def term_present(text: str, patterns: List[str]) -> bool:
    normalized = normalize_text(text)
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)


def extract_skills(text: str) -> List[str]:
    """Use the same canonical skill catalogue as resume parsing."""
    found = []
    for skill, aliases in SKILL_ALIASES.items():
        if any(resume_term_in_text(alias, text) for alias in aliases):
            found.append(skill)
    return sorted(set(found), key=str.lower)


def extract_roles(text: str) -> List[str]:
    found = []

    # Role scoring is intentionally conservative. A JD may mention data scientists,
    # engineers or managers as collaborators without making that the target role.
    for raw_line in str(text or "").splitlines():
        line = clean_line(raw_line)
        normalized = normalize_text(line)
        if not line:
            continue

        role_context = (
            len(line.split()) <= 8
            or any(marker in normalized for marker in (
                "job title", "position", "role", "looking for", "hiring", "seeking"
            ))
        )
        if not role_context:
            continue

        for role, patterns in ROLE_PATTERNS.items():
            if term_present(line, patterns):
                found.append(role)

    return unique(found)


def extract_general_requirements(text: str) -> List[str]:
    found = []
    for requirement, patterns in GENERAL_PATTERNS.items():
        if term_present(text, patterns):
            found.append(requirement)
    return unique(found)


def section_from_heading(line: str) -> Optional[str]:
    value = normalize_heading(line)
    if not value or len(value.split()) > 7:
        return None

    for section, headings in SECTION_HEADINGS.items():
        if value in headings:
            return section
        if any(value.startswith(f"{heading} ") for heading in headings if len(heading.split()) >= 2):
            return section
    return None


def is_metadata_line(line: str) -> bool:
    value = normalize_text(clean_line(line))
    if not value:
        return True
    if any(value.startswith(prefix + ":") or value == prefix for prefix in METADATA_PREFIXES):
        return True
    if re.match(r"^(requisition|job|reference|req)\s*(id|code)\b", value):
        return True
    return False


def classify_requirement(line: str, section: str) -> str:
    normalized = normalize_text(line)

    if any(marker in normalized for marker in PREFERRED_MARKERS):
        return "preferred"
    if section == "preferred":
        return "preferred"
    if section == "required":
        return "required"
    if section == "responsibility":
        return "responsibility"
    if any(marker in normalized for marker in REQUIRED_MARKERS):
        return "required"

    # Unheaded bullet points in JDs are normally responsibilities/requirements.
    return "responsibility"


def classify_requirement_category(line: str) -> str:
    normalized = normalize_text(line)

    if extract_experience_requirement(line) is not None:
        return "experience"
    if is_education_requirement(line):
        return "education"
    if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in SOFT_SKILL_PATTERNS):
        return "soft_skill"
    if extract_skills(line) or extract_general_requirements(line):
        return "technical"
    return "responsibility"


def normalize_keyword(token: str) -> str:
    token = token.lower().strip("._-/+&#")
    if len(token) > 5 and token.endswith("ies"):
        token = token[:-3] + "y"
    elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        token = token[:-1]
    return token


def extract_requirement_keywords(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}", clean_line(text))
    result = []
    seen = set()

    for token in tokens:
        normalized = normalize_keyword(token)
        if len(normalized) < 2 or normalized in STOPWORDS:
            continue
        if normalized.isdigit() or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)

    return result


def extract_requirement_lines(text: str) -> List[Dict]:
    result = []
    current_section = "other"

    for raw_line in text.splitlines():
        line = clean_line(raw_line)
        if not line:
            continue

        heading_section = section_from_heading(line)
        if heading_section:
            current_section = heading_section
            continue

        if current_section == "ignore" or is_metadata_line(line):
            continue

        # Ignore very short standalone labels that are unlikely to be requirements.
        if len(line.split()) <= 2 and not extract_skills(line):
            continue

        requirement_type = classify_requirement(line, current_section)
        category = classify_requirement_category(line)
        skills = extract_skills(line)
        general_requirements = extract_general_requirements(line)
        keywords = extract_requirement_keywords(line)

        measurable = category != "soft_skill" and bool(skills or general_requirements or keywords)

        result.append({
            "text": line,
            "type": requirement_type,
            "category": category,
            "measurable": measurable,
            "skills": skills,
            "roles": extract_roles(line),
            "general_requirements": general_requirements,
            "keywords": keywords,
        })

    return result


def extract_experience_requirement(text: str) -> Optional[float]:
    normalized = normalize_text(text)
    candidates = []

    range_patterns = [
        r"\b(?:minimum\s+)?(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*years?\b(?:\s+of)?(?:\s+[a-z-]+){0,4}\s+experience\b",
        r"\bexperience\s+(?:of|:)?\s*(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*years?\b",
    ]
    minimum_patterns = [
        r"\bminimum(?:\s+of)?\s+(\d+(?:\.\d+)?)\s*\+?\s*years?\b(?:\s+of)?(?:\s+[a-z-]+){0,4}\s+experience\b",
        r"\bat\s+least\s+(\d+(?:\.\d+)?)\s*\+?\s*years?\b(?:\s+of)?(?:\s+[a-z-]+){0,4}\s+experience\b",
        r"\b(\d+(?:\.\d+)?)\s*\+\s*years?\b(?:\s+of)?(?:\s+[a-z-]+){0,4}\s+experience\b",
        r"\b(\d+(?:\.\d+)?)\s*years?\b(?:\s+of)?(?:\s+[a-z-]+){0,4}\s+experience\b",
        r"\bexperience\s+(?:of|:)?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?\b",
    ]

    range_spans = []
    for pattern in range_patterns:
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            candidates.append(float(match.group(1)))
            range_spans.append(match.span())

    for pattern in minimum_patterns:
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            # Do not treat the upper bound of an already parsed range as a
            # separate minimum (for example the "4 years" inside "3-4 years").
            if any(start <= match.start() < end for start, end in range_spans):
                continue
            if match.start() > 0 and normalized[match.start() - 1] == "-":
                continue
            candidates.append(float(match.group(1)))

    return max(candidates) if candidates else None


def extract_alternative_groups(text: str) -> List[Dict]:
    groups = []

    for raw_line in text.splitlines():
        line = clean_line(raw_line)
        normalized = normalize_text(line)
        if not line:
            continue

        skills = unique(extract_skills(line))
        options = []
        allow_equivalent = bool(re.search(r"\bor\s+(?:similar|equivalent|comparable)\b", normalized))

        # Explicit lists such as "one of AWS, Azure, GCP".
        if any(marker in normalized for marker in ("one or more of", "one of", "any of", "either")):
            options = skills

        # Ordinary alternative wording such as "AWS, Azure, or GCP" or
        # "Python or Java for backend services".
        elif re.search(r"\bor\b", normalized):
            left, right = re.split(r"\bor\b", line, maxsplit=1, flags=re.IGNORECASE)
            left_options = extract_skills(left)
            right_head = re.split(r"\b(?:for|with|using|to|while|where|and)\b", right, maxsplit=1, flags=re.IGNORECASE)[0]
            right_options = extract_skills(right_head)
            options = unique(left_options + right_options)

        # "Terraform or similar tools" still represents an alternative
        # requirement even when only one named example is present.
        elif allow_equivalent:
            options = skills

        if len(options) >= 2 or (allow_equivalent and options):
            groups.append({
                "options": options,
                "matched": [],
                "satisfied": False,
                "source": line,
                "type": "alternative",
                "allow_equivalent": allow_equivalent,
            })

    final_groups = []
    seen = set()
    for group in groups:
        key = (
            tuple(normalize_text(option) for option in group["options"]),
            normalize_text(group.get("source", "")),
        )
        if key not in seen:
            seen.add(key)
            final_groups.append(group)
    return final_groups


def is_education_requirement(line: str) -> bool:
    normalized = normalize_text(line)
    patterns = (
        r"\bbachelor(?:'s)?\b", r"\bmaster(?:'s)?\b", r"\bdegree\b", r"\bdiploma\b",
        r"\bgraduate\b", r"\bundergraduate\b", r"\bpostgraduate\b", r"\bstudies\s+in\b",
        r"\bacademic qualification\b", r"\bcomparable qualification\b", r"\bequivalent qualification\b",
        r"\bbca\b", r"\bmca\b", r"\bmba\b", r"\bb\.?tech\b", r"\bb\.e\.?\b",
        r"\bb\.?sc\b", r"\bm\.?sc\b", r"\bb\.?com\b", r"\bm\.?com\b",
        r"\bllb\b", r"\bllm\b", r"\bmbbs\b", r"\bb\.?pharm\b", r"\bm\.?pharm\b",
    )
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)


def extract_education_requirements(text: str) -> List[Dict]:
    requirements = []

    for raw_line in text.splitlines():
        line = clean_line(raw_line)
        if not line or not is_education_requirement(line):
            continue

        normalized = normalize_text(line)
        level = "generic"
        if re.search(r"\bmaster(?:'s)?\b|\bpostgraduate\b|\bmca\b|\bmba\b|\bm\.?sc\b|\bm\.?com\b|\bllm\b|\bm\.?pharm\b", normalized):
            level = "master"
        elif re.search(r"\bbachelor(?:'s)?\b|\bundergraduate\b|\bbca\b|\bb\.?tech\b|\bb\.e\.?\b|\bb\.?sc\b|\bb\.?com\b|\bllb\b|\bmbbs\b|\bb\.?pharm\b", normalized):
            level = "bachelor"
        elif re.search(r"\bdiploma\b", normalized):
            level = "diploma"

        allows_related = bool(re.search(
            r"\b(?:related|relevant|comparable|equivalent|similar)\b",
            normalized,
        ))

        field_text = ""
        field_match = re.search(
            r"(?:degree|studies|qualification|bachelor(?:'s)?|master(?:'s)?)\s+(?:in|of)\s+(.+?)(?=\s+or\s+(?:a\s+)?(?:related|relevant|comparable|equivalent)|[.;,]|$)",
            normalized,
            flags=re.IGNORECASE,
        )
        if field_match:
            field_text = field_match.group(1)

        field_keywords = extract_requirement_keywords(field_text) if field_text else []

        requirements.append({
            "text": line,
            "level": level,
            "field_keywords": field_keywords,
            "allows_related": allows_related,
        })

    return requirements


def extract_education(text: str) -> List[str]:
    found = []

    for education, patterns in EDUCATION_PATTERNS.items():
        if term_present(text, patterns):
            found.append(education)

    if extract_education_requirements(text) and not found:
        found.append("Degree or comparable qualification")

    return unique(found)


def remove_alternative_skills_from_required(required_skills, alternative_groups):
    alternative_options = {
        normalize_text(option)
        for group in alternative_groups
        for option in group.get("options", [])
    }
    return [skill for skill in required_skills if normalize_text(skill) not in alternative_options]


def split_required_preferred_skills(requirement_lines, alternative_groups):
    required = []
    preferred = []

    for item in requirement_lines:
        skills = item.get("skills", [])
        if item.get("type") == "preferred":
            preferred.extend(skills)
        else:
            required.extend(skills)

    required = unique(required)
    preferred = unique(preferred)
    required = remove_alternative_skills_from_required(required, alternative_groups)
    preferred = [skill for skill in preferred if skill not in required]
    return required, preferred


def analyze_jd(text: str) -> Dict:
    if not text or not text.strip():
        raise ValueError("Job description is empty.")

    text = text.strip()
    requirement_lines = extract_requirement_lines(text)
    alternative_groups = extract_alternative_groups(text)
    required_skills, preferred_skills = split_required_preferred_skills(
        requirement_lines,
        alternative_groups,
    )

    education_requirements = extract_education_requirements(text)
    measurable_lines = [item for item in requirement_lines if item.get("measurable")]
    unmeasurable_lines = [item for item in requirement_lines if not item.get("measurable")]

    return {
        "text": text,
        "skills": unique(extract_skills(text)),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "general_requirements": extract_general_requirements(text),
        "roles": extract_roles(text),
        "required_years": extract_experience_requirement(text),
        "requirement_lines": requirement_lines,
        "alternative_groups": alternative_groups,
        "education": extract_education(text),
        "education_requirements": education_requirements,
        "requirement_stats": {
            "total": len(requirement_lines),
            "measurable": len(measurable_lines),
            "not_reliably_measurable": len(unmeasurable_lines),
        },
    }
