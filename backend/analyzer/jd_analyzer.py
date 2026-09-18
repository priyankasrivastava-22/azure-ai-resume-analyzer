import re


SKILL_PATTERNS = {
    "Python": [
        r"\bpython\b",
    ],
    "C#": [
    r"(?<![a-z])c\s*#(?![a-z])",
    r"\bc\s*sharp\b",
    ],
    "PowerShell": [
        r"\bpowershell\b",
    ],
    "KQL": [
        r"\bkql\b",
        r"\bkusto\b",
        r"\bkusto query language\b",
    ],
    "AI": [
        r"\bartificial intelligence\b",
        r"\bai\b",
    ],
    "ML": [
        r"\bmachine learning\b",
        r"\bml\b",
    ],
    "LLM": [
        r"\blarge language models?\b",
        r"\bllms?\b",
    ],
    "MCP": [
        r"\bmodel context protocol\b",
        r"\bmcp\b",
    ],
    "Azure": [
        r"\bmicrosoft azure\b",
        r"\bazure\b",
    ],
    "ServiceNow": [
        r"\bservicenow\b",
    ],
    "PagerDuty": [
        r"\bpagerduty\b",
    ],
    "ICM": [
        r"\bicm\b",
        r"\bincident management\b",
    ],
    "Grafana": [
        r"\bgrafana\b",
    ],
    "Geneva": [
        r"\bgeneva\b",
    ],
    "Power BI": [
        r"\bpower\s*bi\b",
        r"\bpowerbi\b",
    ],
    "Microsoft Fabric": [
        r"\bmicrosoft fabric\b",
        r"\bms fabric\b",
    ],
    "Application Insights": [
        r"\bapplication insights\b",
    ],
    "Prometheus": [
        r"\bprometheus\b",
    ],
    "OpenTelemetry": [
        r"\bopentelemetry\b",
        r"\bopen telemetry\b",
    ],
    "Splunk": [
        r"\bsplunk\b",
    ],
    "Datadog": [
        r"\bdatadog\b",
    ],
    "Jenkins": [
        r"\bjenkins\b",
    ],
    "Git": [
        r"\bgit\b",
    ],
    "GitHub": [
        r"\bgithub\b",
    ],
    "GitHub Actions": [
        r"\bgithub actions\b",
    ],
    "Azure DevOps": [
        r"\bazure devops\b",
    ],
    "Docker": [
        r"\bdocker\b",
    ],
    "Kubernetes": [
        r"\bkubernetes\b",
        r"\bk8s\b",
    ],
    "Terraform": [
        r"\bterraform\b",
    ],
    "Ansible": [
        r"\bansible\b",
    ],
    "Linux": [
        r"\blinux\b",
    ],
    "SQL": [
        r"\bsql\b",
    ],
    "PL/SQL": [
        r"\bpl\s*/?\s*sql\b",
    ],
    "PostgreSQL": [
        r"\bpostgresql\b",
        r"\bpostgres\b",
    ],
    "Oracle": [
        r"\boracle\b",
    ],
    "MySQL": [
        r"\bmysql\b",
    ],
    "FastAPI": [
        r"\bfastapi\b",
    ],
    "Flask": [
        r"\bflask\b",
    ],
    "React": [
        r"\breact(?:\.js|js)?\b",
    ],
    "Node.js": [
        r"\bnode(?:\.js|js)?\b",
    ],
    "Java": [
        r"\bjava\b",
    ],
    "Spring": [
        r"\bspring\b",
    ],
    "Maven": [
        r"\bmaven\b",
    ],
    "REST API": [
        r"\brest(?:ful)?\s+apis?\b",
        r"\brestful\b",
    ],
    "CI/CD": [
        r"\bci\s*/\s*cd\b",
        r"\bcontinuous integration\b",
        r"\bcontinuous delivery\b",
        r"\bcontinuous deployment\b",
    ],
    "Microservices": [
        r"\bmicroservices?\b",
    ],
}


ROLE_PATTERNS = {
    "SRE": [
        r"\bsite reliability\b",
        r"\bsite reliability engineer(?:ing)?\b",
        r"\bsre\b",
    ],
    "Software Engineer": [
        r"\bsoftware engineer(?:ing)?\b",
        r"\bsoftware developer\b",
        r"\bsoftware development\b",
    ],
    "DevOps Engineer": [
        r"\bdevops engineer(?:ing)?\b",
        r"\bdevops\b",
    ],
    "Platform Engineer": [
        r"\bplatform engineer(?:ing)?\b",
        r"\bplatform engineering\b",
    ],
    "Cloud Engineer": [
        r"\bcloud engineer(?:ing)?\b",
        r"\bcloud services?\b",
    ],
    "Backend Engineer": [
        r"\bbackend engineer(?:ing)?\b",
        r"\bback[- ]end engineer(?:ing)?\b",
    ],
    "Automation Engineer": [
        r"\bautomation engineer(?:ing)?\b",
    ],
}


GENERAL_PATTERNS = {
    "incident management": [
        r"\bincident management\b",
        r"\bincident response\b",
        r"\bincident handling\b",
    ],
    "monitoring": [
        r"\bmonitoring\b",
        r"\bmonitor\b",
        r"\bapplication monitoring\b",
    ],
    "alerting": [
        r"\balerting\b",
        r"\balerts?\b",
    ],
    "observability": [
        r"\bobservability\b",
    ],
    "on-call": [
        r"\bon[- ]call\b",
    ],
    "log analysis": [
        r"\blog analysis\b",
        r"\blog traversal\b",
        r"\blog investigation\b",
        r"\bapplication logs?\b",
    ],
    "production troubleshooting": [
        r"\bproduction troubleshooting\b",
        r"\btroubleshoot(?:ing)? production\b",
        r"\bproduction support\b",
        r"\bproduction issues?\b",
    ],
    "root cause analysis": [
        r"\broot cause analysis\b",
        r"\brca\b",
    ],
    "automation": [
        r"\bautomation\b",
        r"\bautomated\b",
        r"\bautomate\b",
    ],
    "cloud services": [
        r"\bcloud services?\b",
        r"\bcloud infrastructure\b",
        r"\bcloud platform\b",
    ],
    "continuous improvement": [
        r"\bcontinuous improvement\b",
    ],
    "customer communication": [
        r"\bcustomer communication\b",
        r"\bcustomer-facing\b",
        r"\bcommunicat\w*\b.{0,40}\bcustomer",
    ],
    "escalation": [
        r"\bescalation\b",
        r"\bescalate\b",
    ],
    "SLA management": [
        r"\bslas?\b",
        r"\bservice level agreements?\b",
    ],
}


EDUCATION_PATTERNS = {
    "BCA": [
        r"\bbca\b",
        r"\bbachelor(?:'s)?\s+of\s+computer\s+applications?\b",
    ],
    "MCA": [
        r"\bmca\b",
        r"\bmaster(?:'s)?\s+of\s+computer\s+applications?\b",
    ],
    "B.Tech": [
        r"\bb\.?\s*tech\b",
        r"\bbachelor(?:'s)?\s+of\s+technology\b",
    ],
    "BE": [
        r"\bb\.?\s*e\.?\b",
        r"\bbachelor(?:'s)?\s+of\s+engineering\b",
    ],
    "Bachelor's degree": [
        r"\bbachelor(?:'s)?\s+degree\b",
        r"\bundergraduate degree\b",
    ],
    "Master's degree": [
        r"\bmaster(?:'s)?\s+degree\b",
        r"\bpostgraduate degree\b",
    ],
}


def normalize_text(text):
    text = text or ""

    text = text.lower()

    text = (
        text.replace("–", "-")
        .replace("—", "-")
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def unique(items):
    result = []

    for item in items or []:
        if item not in result:
            result.append(item)

    return result


def term_present(
    text,
    patterns,
):
    normalized = normalize_text(
        text
    )

    for pattern in patterns:
        if re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        ):
            return True

    return False


def extract_skills(text):
    found = []

    for skill, patterns in (
        SKILL_PATTERNS.items()
    ):
        if term_present(
            text,
            patterns,
        ):
            found.append(skill)

    return found


def extract_roles(text):
    found = []

    for role, patterns in (
        ROLE_PATTERNS.items()
    ):
        if term_present(
            text,
            patterns,
        ):
            found.append(role)

    return found


def extract_general_requirements(
    text
):
    found = []

    for requirement, patterns in (
        GENERAL_PATTERNS.items()
    ):
        if term_present(
            text,
            patterns,
        ):
            found.append(requirement)

    return found


def is_preferred_heading(line):
    value = normalize_text(line)

    return (
        value == "preferred"
        or value.startswith(
            "preferred qualifications"
        )
        or value.startswith(
            "preferred experience"
        )
        or value.startswith(
            "preferred requirements"
        )
        or value.startswith(
            "nice to have"
        )
    )


def is_required_heading(line):
    value = normalize_text(line)

    return (
        value == "requirements"
        or value == "qualifications"
        or value.startswith(
            "required qualifications"
        )
        or value.startswith(
            "required experience"
        )
        or value.startswith(
            "minimum qualifications"
        )
    )


def classify_requirement(
    line,
    section,
):
    normalized = normalize_text(
        line
    )

    if section == "preferred":
        return "preferred"

    if section == "required":
        return "required"

    preferred_markers = [
        "preferred",
        "nice to have",
        "nice-to-have",
        "good to have",
        "bonus",
        "desired",
        "plus",
    ]

    for marker in preferred_markers:
        if marker in normalized:
            return "preferred"

    return "required"


def extract_requirement_lines(
    text
):
    result = []

    current_section = "required"

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if is_preferred_heading(line):
            current_section = "preferred"
            continue

        if is_required_heading(line):
            current_section = "required"
            continue

        classification = classify_requirement(
            line,
            current_section,
        )

        result.append(
            {
                "text": line,
                "type": classification,
                "skills": extract_skills(
                    line
                ),
                "roles": extract_roles(
                    line
                ),
                "general_requirements": (
                    extract_general_requirements(
                        line
                    )
                ),
            }
        )

    return result


def extract_experience_requirement(
    text
):
    normalized = normalize_text(
        text
    )

    candidates = []

    patterns = [
        r"\bminimum\s+of\s+(\d+(?:\.\d+)?)\s*\+?\s*years?",
        r"\bat\s+least\s+(\d+(?:\.\d+)?)\s*\+?\s*years?",
        r"\b(\d+(?:\.\d+)?)\s*\+\s*years?",
    ]

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        ):
            try:
                candidates.append(
                    float(match.group(1))
                )
            except ValueError:
                pass

    if not candidates:
        return None

    return max(candidates)


def extract_alternative_groups(text):
    groups = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        normalized = normalize_text(line)

        # These phrases indicate that the listed options
        # are alternatives rather than individually required.
        alternative_markers = [
            "one or more of",
            "one of",
            "any of",
            "either",
            "or similar",
            "or equivalent",
        ]

        has_alternative = any(
            marker in normalized
            for marker in alternative_markers
        )

        if not has_alternative:
            continue

        skills = extract_skills(line)

        # Remove accidental duplicate skills while
        # preserving their original order.
        skills = unique(skills)

        if len(skills) >= 2:
            groups.append(
                {
                    "options": skills,
                    "matched": [],
                    "satisfied": False,
                    "source": line,
                    "type": "alternative",
                }
            )

    # Remove duplicate groups while preserving order.
    final_groups = []
    seen = set()

    for group in groups:
        key = tuple(
            normalize_text(option)
            for option in group["options"]
        )

        if key in seen:
            continue

        seen.add(key)
        final_groups.append(group)

    return final_groups


def extract_education(text):
    found = []

    for education, patterns in (
        EDUCATION_PATTERNS.items()
    ):
        if term_present(
            text,
            patterns,
        ):
            found.append(
                education
            )

    return unique(found)


def remove_alternative_skills_from_required(
    required_skills,
    alternative_groups,
):
    alternative_options = set()

    for group in alternative_groups:
        for option in group.get(
            "options",
            [],
        ):
            alternative_options.add(
                normalize_text(option)
            )

    return [
        skill
        for skill in required_skills
        if normalize_text(skill)
        not in alternative_options
    ]


def split_required_preferred_skills(
    requirement_lines,
    alternative_groups,
):
    required = []
    preferred = []

    for item in requirement_lines:
        skills = item.get(
            "skills",
            [],
        )

        if item.get("type") == "preferred":
            preferred.extend(skills)
        else:
            required.extend(skills)

    required = unique(required)
    preferred = unique(preferred)

    # Skills belonging to "one or more of / or similar"
    # are represented by the alternative group instead
    # of being treated as individually mandatory.
    required = (
        remove_alternative_skills_from_required(
            required,
            alternative_groups,
        )
    )

    # A skill cannot simultaneously be required
    # and preferred.
    preferred = [
        skill
        for skill in preferred
        if skill not in required
    ]

    return (
        required,
        preferred,
    )


def analyze_jd(text):
    if not text or not text.strip():
        raise ValueError(
            "Job description is empty."
        )

    text = text.strip()

    requirement_lines = (
        extract_requirement_lines(
            text
        )
    )

    alternative_groups = (
        extract_alternative_groups(
            text
        )
    )

    required_skills, preferred_skills = (
        split_required_preferred_skills(
            requirement_lines,
            alternative_groups,
        )
    )

    # Determine all skills from the JD,
    # but keep required/preferred classification separate.
    all_skills = unique(
        extract_skills(text)
    )

    general_requirements = (
        extract_general_requirements(
            text
        )
    )

    roles = extract_roles(text)

    required_years = (
        extract_experience_requirement(
            text
        )
    )

    education = extract_education(
        text
    )

    return {
        "text": text,

        "skills": all_skills,

        "required_skills": (
            required_skills
        ),

        "preferred_skills": (
            preferred_skills
        ),

        "general_requirements": (
            general_requirements
        ),

        "roles": roles,

        "required_years": (
            required_years
        ),

        "requirement_lines": (
            requirement_lines
        ),

        "alternative_groups": (
            alternative_groups
        ),

        "education": education,
    }