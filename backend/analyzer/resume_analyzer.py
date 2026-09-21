import re
from datetime import date
from typing import Dict, List, Optional, Tuple

SKILL_ALIASES = {
    "Python": ["python"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "C": [r"\bc\b"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "c sharp", "csharp"],
    "PowerShell": ["powershell", "pwsh"],
    "Bash": ["bash", "bash scripting", "shell scripting", "shell script"],
    "KQL": ["kql", "kusto", "kusto query language"],
    "SQL": ["sql"],
    "PL/SQL": ["pl/sql", "plsql"],
    "React": ["react", "reactjs"],
    "Angular": ["angular"],
    "Vue": ["vue", "vuejs"],
    "Node.js": ["node.js", "nodejs"],
    "Express": ["express.js", "express"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Spring": ["spring framework", "spring"],
    "Spring Boot": ["spring boot"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform"],
    "Ansible": ["ansible"],
    "Jenkins": ["jenkins"],
    "Git": ["git"],
    "GitHub": ["github"],
    "GitLab": ["gitlab"],
    "Azure": ["azure", "microsoft azure"],
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud"],
    "Linux": ["linux"],
    "RHEL": ["rhel", "red hat enterprise linux"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "Oracle": ["oracle database", "oracle"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Cosmos DB": ["cosmos db", "azure cosmos db"],
    "REST API": ["rest api", "restful api", "rest"],
    "GraphQL": ["graphql"],
    "CI/CD": ["ci/cd", "continuous integration", "continuous deployment"],
    "GitHub Actions": ["github actions"],
    "Azure DevOps": ["azure devops"],
    "Prometheus": ["prometheus"],
    "Grafana": ["grafana"],
    "Geneva": ["geneva monitoring", "geneva"],
    "Power BI": ["power bi", "powerbi"],
    "Microsoft Fabric": ["microsoft fabric"],
    "ADF": ["azure data factory", "adf"],
    "Synapse": ["synapse", "azure synapse"],
    "ServiceNow": ["servicenow", "service now"],
    "PagerDuty": ["pagerduty", "pager duty"],
    "Jira": ["jira"],
    "Splunk": ["splunk"],
    "Datadog": ["datadog"],
    "New Relic": ["new relic"],
    "Application Insights": ["application insights"],
    "OpenTelemetry": ["opentelemetry", "open telemetry"],
    "Kafka": ["kafka", "apache kafka"],
    "RabbitMQ": ["rabbitmq"],
    "Maven": ["maven"],
    "Gradle": ["gradle"],
    "Nginx": ["nginx"],
    "Helm": ["helm"],
    "Istio": ["istio"],
    "Microservices": ["microservices", "microservices architecture"],
    "AI": ["artificial intelligence", "genai", "ai"],
    "ML": ["machine learning", "ml"],
    "LLM": ["large language model", "large language models", "llm", "llms"],
    "GenAI": ["generative ai", "genai"],
    "MCP": ["model context protocol", "mcp"]
}

ROLES = [
    "Software Engineer",
    "DevOps Engineer",
    "SRE",
    "Platform Engineer",
    "Backend Engineer",
    "Cloud Engineer",
    "Automation Engineer"
]

ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "created", "automated",
    "engineered", "deployed", "configured", "managed", "optimized", "reduced",
    "improved", "integrated", "secured", "migrated", "monitored", "analyzed",
    "resolved", "implemented", "maintained", "provisioned", "led", "delivered"
}

WEAK_VERBS = {
    "worked", "helped", "assisted", "responsible", "involved", "participated"
}

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12
}

MONTH_PATTERN = r"(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
YEAR_PATTERN = r"(?:19|20)\d{2}"

DATE_TOKEN_PATTERN = rf"(?:{MONTH_PATTERN}\s+{YEAR_PATTERN}|\d{{1,2}}[/-]\d{{4}}|{YEAR_PATTERN})"

DATE_RANGE_PATTERNS = [
    re.compile(rf"(?P<start>{DATE_TOKEN_PATTERN})\s*(?:-|–|—|to|until|through)\s*(?P<end>{DATE_TOKEN_PATTERN}|present|current|now)", re.I),
    re.compile(rf"(?P<start>{DATE_TOKEN_PATTERN})\s+(?:to|until|through)\s+(?P<end>{DATE_TOKEN_PATTERN}|present|current|now)", re.I)
]

def normalize_text(text: str) -> str:
    text = text or ""
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def term_in_text(term: str, text: str) -> bool:
    if not term or not text:
        return False
    normalized = normalize_text(text).lower()
    term_lower = term.lower()
    if term_lower == "c":
        return bool(re.search(r"(?<![a-z0-9+#])c(?![a-z0-9+#])", normalized))
    if term_lower == "c#":
        return bool(re.search(r"(?<![a-z0-9])c#(?![a-z0-9])", normalized))
    if term_lower == "c++":
        return bool(re.search(r"(?<![a-z0-9])c\+\+(?![a-z0-9])", normalized))
    if term_lower in {"ai", "ml"}:
        return bool(re.search(rf"(?<![a-z]){re.escape(term_lower)}(?![a-z])", normalized))
    if term_lower == "kql":
        return bool(re.search(r"\b(?:kql|kusto|kusto query language)\b", normalized))
    pattern = r"(?<![a-z0-9])" + re.escape(term_lower) + r"(?![a-z0-9])"
    return bool(re.search(pattern, normalized))

def extract_skills(text: str) -> List[str]:
    normalized = normalize_text(text)
    found = []
    for skill, aliases in SKILL_ALIASES.items():
        if any(term_in_text(alias, normalized) for alias in aliases):
            found.append(skill)
    return sorted(set(found), key=str.lower)


# Extract explicit skills from the resume's Skills section without relying on a fixed domain catalogue.
def extract_explicit_skill_terms(skills_text: str) -> List[str]:
    if not skills_text:
        return []

    blocked = {
        "skills", "technical skills", "core skills", "technologies", "technical expertise",
        "professional skills", "tools", "platforms", "frameworks", "languages",
    }
    candidates = []

    for raw_line in skills_text.splitlines():
        line = raw_line.strip().lstrip("•●▪◦*- ")
        if not line:
            continue

        # Drop category labels such as "Cloud & Infrastructure:" and keep the listed values.
        if ":" in line:
            _, line = line.split(":", 1)

        for part in re.split(r"[,;|•]", line):
            value = re.sub(r"\s+", " ", part).strip(" .:-")
            normalized = value.lower()

            if not value or normalized in blocked:
                continue
            if "@" in value or re.search(r"https?://|www\.", value, flags=re.I):
                continue
            if len(value) < 2 or len(value) > 60:
                continue
            if len(value.split()) > 7:
                continue
            if re.fullmatch(r"\d+(?:[./-]\d+)*", value):
                continue

            candidates.append(value)

    result = []
    seen = set()
    for item in candidates:
        key = normalize_text(item).lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

def extract_email(text: str) -> Optional[str]:
    match = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text or "", re.I)
    return match.group(0) if match else None

def extract_phone(text: str) -> Optional[str]:
    matches = re.findall(r"(?:\+?\d[\d\s().-]{8,}\d)", text or "")
    for value in matches:
        digits = re.sub(r"\D", "", value)
        if 10 <= len(digits) <= 15:
            return value.strip()
    return None

def extract_name(text: str) -> Optional[str]:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    for line in lines[:8]:
        cleaned = re.sub(r"[^A-Za-z .'-]", "", line).strip()
        if 2 <= len(cleaned.split()) <= 5 and len(cleaned) >= 4:
            lower = cleaned.lower()
            if not any(x in lower for x in ["resume", "curriculum", "engineer", "developer", "github", "linkedin"]):
                return cleaned
    return None

def month_to_number(value: str) -> Optional[int]:
    value = value.lower().strip().rstrip(".")
    if value in MONTHS:
        return MONTHS[value]
    if len(value) >= 3:
        for name, number in MONTHS.items():
            if name.startswith(value):
                return number
    return None

def parse_date_token(token: str) -> Optional[Tuple[int, int]]:
    token = normalize_text(token).lower().strip()
    token = token.rstrip(".,")
    if re.fullmatch(r"\d{1,2}[/-]\d{4}", token):
        month, year = re.split(r"[/-]", token)
        month = int(month)
        year = int(year)
        if 1 <= month <= 12:
            return year, month
    match = re.fullmatch(rf"({MONTH_PATTERN})\s+({YEAR_PATTERN})", token, re.I)
    if match:
        month = month_to_number(match.group(1))
        year = int(match.group(2))
        if month:
            return year, month
    if re.fullmatch(YEAR_PATTERN, token):
        return int(token), 1
    return None

def parse_date_range(text: str) -> Optional[Tuple[Tuple[int, int], Optional[Tuple[int, int]], str]]:
    normalized = normalize_text(text)
    for pattern in DATE_RANGE_PATTERNS:
        match = pattern.search(normalized)
        if not match:
            continue
        start = parse_date_token(match.group("start"))
        end_token = match.group("end").lower()
        if end_token in {"present", "current", "now"}:
            end = None
        else:
            end = parse_date_token(end_token)
        if start:
            return start, end, match.group(0)
    return None

def parse_date_ranges(text: str) -> List[Tuple[Tuple[int, int], Optional[Tuple[int, int]], str]]:
    normalized = normalize_text(text)
    results = []
    occupied = []
    for pattern in DATE_RANGE_PATTERNS:
        for match in pattern.finditer(normalized):
            start = parse_date_token(match.group("start"))
            end_token = match.group("end").lower()
            end = None if end_token in {"present", "current", "now"} else parse_date_token(end_token)
            if not start:
                continue
            span = match.span()
            if any(span[0] < existing[1] and span[1] > existing[0] for existing in occupied):
                continue
            occupied.append(span)
            results.append((start, end, match.group(0)))
    return results

def parse_date_range_flexible(text: str) -> Optional[Tuple[Tuple[int, int], Optional[Tuple[int, int]], str]]:
    result = parse_date_range(text)
    if result:
        return result
    normalized = normalize_text(text)
    matches = list(re.finditer(DATE_TOKEN_PATTERN, normalized, re.I))
    if len(matches) >= 2:
        start_token = matches[0].group(0)
        end_token = matches[1].group(0)
        start = parse_date_token(start_token)
        end = parse_date_token(end_token)
        if start and end and start <= end:
            return start, end, f"{start_token} - {end_token}"
    if len(matches) >= 1 and re.search(r"\b(?:present|current|now)\b", normalized, re.I):
        start = parse_date_token(matches[0].group(0))
        if start:
            return start, None, f"{matches[0].group(0)} - Present"
    return None

def month_index(year: int, month: int) -> int:
    return year * 12 + month

def calculate_duration_months(start: Tuple[int, int], end: Optional[Tuple[int, int]]) -> int:
    if end is None:
        today = date.today()
        end = (today.year, today.month)
    start_index = month_index(start[0], start[1])
    end_index = month_index(end[0], end[1])
    return max(0, end_index - start_index + 1)

def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        previous_start, previous_end = merged[-1]
        if start <= previous_end + 1:
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged

def calculate_experience_years(intervals: List[Tuple[Tuple[int, int], Optional[Tuple[int, int]]]]) -> Optional[float]:
    if not intervals:
        return None
    month_intervals = []
    for start, end in intervals:
        start_index = month_index(start[0], start[1])
        if end is None:
            today = date.today()
            end_index = month_index(today.year, today.month)
        else:
            end_index = month_index(end[0], end[1])
        if end_index >= start_index:
            month_intervals.append((start_index, end_index))
    merged = merge_intervals(month_intervals)
    total_months = sum(end - start + 1 for start, end in merged)
    return round(total_months / 12, 2)

def extract_education(text: str) -> List[str]:
    normalized = normalize_text(text).lower()
    education = []
    patterns = {
        "BCA": r"\bbca\b|bachelor of computer applications",
        "MCA": r"\bmca\b|master of computer applications",
        "B.Tech": r"\bb\.?tech\b|bachelor of technology",
        "M.Tech": r"\bm\.?tech\b|master of technology",
        "B.E.": r"\bb\.?e\.?\b|bachelor of engineering",
        "M.E.": r"\bm\.?e\.?\b|master of engineering",
        "MBA": r"\bmba\b|master of business administration",
        "B.Sc": r"\bb\.?sc\b|bachelor of science",
        "M.Sc": r"\bm\.?sc\b|master of science",
        "PhD": r"\bph\.?d\b|doctor of philosophy"
    }
    for degree, pattern in patterns.items():
        if re.search(pattern, normalized, re.I):
            education.append(degree)
    return education

def extract_bullets(text: str) -> List[str]:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    bullets = []
    for line in lines:
        if re.match(r"^[•●▪◦*-]\s*", line):
            bullets.append(re.sub(r"^[•●▪◦*-]\s*", "", line).strip())
    return bullets

def quantified_result_count(text: str) -> int:
    patterns = [
        r"\b\d+%",
        r"\b\d+\+",
        r"\b\d+\s*(?:users|employees|servers|systems|applications|environments|projects|teams|months|years|days|hours|minutes|incidents|releases|deployments)\b",
        r"\bfrom\s+\d+\s+to\s+\d+\b",
        r"\bmore than\s+\d+\b",
        r"\bfewer than\s+\d+\b"
    ]
    return sum(len(re.findall(pattern, text or "", re.I)) for pattern in patterns)

def analyze_experience_quality(experience_text: str) -> Dict:
    bullets = extract_bullets(experience_text)
    if not bullets:
        bullets = [line.strip() for line in experience_text.splitlines() if line.strip() and not parse_date_range_flexible(line)]
    total = len(bullets)
    action_count = 0
    technology_count = 0
    quantified_count = 0
    weak_count = 0
    technology_words = [skill.lower() for skill in SKILL_ALIASES]
    for bullet in bullets:
        words = re.findall(r"\b[A-Za-z]+\b", bullet.lower())
        if words and words[0] in ACTION_VERBS:
            action_count += 1
        if any(term_in_text(skill, bullet) for skill in technology_words):
            technology_count += 1
        if quantified_result_count(bullet):
            quantified_count += 1
        if any(re.search(rf"\b{re.escape(verb)}\b", bullet.lower()) for verb in WEAK_VERBS):
            weak_count += 1
    return {
        "bullet_count": total,
        "action_verb_ratio": round(action_count / total * 100) if total else 0,
        "technology_ratio": round(technology_count / total * 100) if total else 0,
        "quantified_ratio": round(quantified_count / total * 100) if total else 0,
        "weak_verb_ratio": round(weak_count / total * 100) if total else 0,
        "quality_score": min(100, round(
            (action_count / total * 40 if total else 0) +
            (technology_count / total * 30 if total else 0) +
            (quantified_count / total * 30 if total else 0)
        ))
    }

def extract_roles(text: str) -> List[str]:
    found = []
    normalized = normalize_text(text)
    for role in ROLES:
        if term_in_text(role, normalized):
            found.append(role)
    return found

def split_experience_entries(experience_text: str) -> List[Dict]:
    lines = [line.strip() for line in (experience_text or "").splitlines() if line.strip()]
    entries = []
    current = None
    for index, line in enumerate(lines):
        date_range = parse_date_range_flexible(line)
        if date_range:
            if current:
                current["date_range"] = date_range
                entries.append(current)
                current = None
            else:
                entries.append({
                    "header": line,
                    "date_range": date_range,
                    "lines": []
                })
            continue
        if current is None:
            current = {
                "header": line,
                "date_range": None,
                "lines": []
            }
        else:
            current["lines"].append(line)
    if current:
        entries.append(current)
    valid = []
    for entry in entries:
        combined = " ".join([entry.get("header", "")] + entry.get("lines", []))
        date_range = entry.get("date_range") or parse_date_range_flexible(combined)
        if date_range:
            valid.append({
                "header": entry.get("header", ""),
                "date_range": date_range,
                "text": combined
            })
    return valid

def extract_experience_entries(experience_text: str) -> List[Dict]:
    lines = [line.strip() for line in (experience_text or "").splitlines() if line.strip()]
    entries = []
    for index, line in enumerate(lines):
        date_range = parse_date_range_flexible(line)
        if not date_range:
            continue
        previous_lines = lines[max(0, index - 2):index + 1]
        header = " ".join(previous_lines)
        title = None
        for role in ROLES:
            if term_in_text(role, header):
                title = role
                break
        if title is None:
            title_match = re.search(
                r"\b(Engineer|Developer|Analyst|Consultant|Associate|Manager|Architect|Administrator|Specialist)\b",
                header,
                re.I
            )
            title = title_match.group(0) if title_match else "Unknown role"
        company = None
        company_match = re.search(
            r"\|\s*([^|]+?)\s*\|\s*(?:[A-Za-z .'-]+,\s*)?(?:India|USA|UK|Canada|Australia)\b",
            header,
            re.I
        )
        if company_match:
            company = company_match.group(1).strip()
        if company is None:
            company_match = re.search(
                r"\b(?:at|@)\s+([A-Z][A-Za-z0-9&().,\- ]{2,})",
                header
            )
            if company_match:
                company = company_match.group(1).strip()
        start, end, raw = date_range
        months = calculate_duration_months(start, end)
        entries.append({
            "title": title,
            "company": company,
            "start": f"{start[0]:04d}-{start[1]:02d}",
            "end": f"{end[0]:04d}-{end[1]:02d}" if end else None,
            "date_range": raw,
            "duration_months": months,
            "duration_years": round(months / 12, 2),
            "confidence": "high"
        })
    return entries

def analyze_resume(text: str, sections: Optional[Dict[str, str]] = None) -> Dict:
    text = text or ""
    sections = sections or {}
    experience_text = sections.get("experience", "")
    education_text = sections.get("education", "")
    skills_text = sections.get("skills", "")
    if not experience_text:
        experience_text = ""
    combined_skill_text = f"{skills_text}\n{text}"
    known_skills = extract_skills(combined_skill_text)
    explicit_skills = extract_explicit_skill_terms(skills_text)

    skills = []
    seen_skills = set()
    for skill in known_skills + explicit_skills:
        key = normalize_text(skill).lower()
        if key and key not in seen_skills:
            seen_skills.add(key)
            skills.append(skill)
    experience_entries = extract_experience_entries(experience_text)
    intervals = []
    for entry in experience_entries:
        start = tuple(map(int, entry["start"].split("-")))
        end = tuple(map(int, entry["end"].split("-"))) if entry["end"] else None
        intervals.append((start, end))
    experience_years = calculate_experience_years(intervals)
    if experience_years is not None:
        years = int(experience_years)
        months = round((experience_years - years) * 12)
        if months >= 12:
            years += 1
            months = 0
        experience_summary = f"Approximately {years} years {months} months of experience identified."
    else:
        experience_summary = "No reliable experience duration identified."
    education = extract_education(education_text or text)
    roles = extract_roles(text)
    experience_quality = analyze_experience_quality(experience_text)
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": skills,
        "experience_years": experience_years,
        "experience_summary": experience_summary,
        "experience_entries": experience_entries,
        "experience_confidence": "high" if experience_entries else "low",
        "education": education,
        "roles": roles,
        "experience_quality": experience_quality
    }