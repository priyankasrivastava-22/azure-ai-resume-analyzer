import re


STANDARD_HEADINGS = {
    "summary",
    "skills",
    "experience",
    "education",
    "projects",
    "certifications",
    "achievements",
}


def analyze_ats(text, sections):
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    issues = []
    positives = []

    section_count = sum(
        1 for section in sections if section in STANDARD_HEADINGS
    )

    section_score = min(100, round((section_count / 5) * 100))

    if section_count >= 4:
        positives.append("Uses several standard resume sections.")
    else:
        issues.append("Several standard resume sections are missing.")

    if not re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    ):
        issues.append("Email address was not detected.")

    else:
        positives.append("Email address detected.")

    if re.search(r"\+?\d[\d\s().-]{8,}\d", text):
        positives.append("Phone number detected.")
    else:
        issues.append("Phone number was not detected.")

    bullet_lines = [
        line
        for line in lines
        if re.match(r"^[•●▪◦*-]\s+", line)
    ]

    if bullet_lines:
        positives.append("Bullet-based content detected.")
    else:
        issues.append("No standard bullet structure detected.")

    repeated_lines = []
    seen = set()

    for line in lines:
        normalized = re.sub(r"\W", "", line.lower())

        if len(normalized) > 20:
            if normalized in seen:
                repeated_lines.append(line)

            seen.add(normalized)

    if repeated_lines:
        issues.append("Repeated lines were detected.")

    if len(text) < 800:
        issues.append("Resume contains relatively little extracted text.")

    if len(text) > 15000:
        issues.append("Resume may contain excessive content.")

    possible_columns = False

    for line in text.splitlines():
        if "\t" in line or re.search(r"\S {5,}\S", line):
            possible_columns = True
            break

    if possible_columns:
        issues.append(
            "Possible multi-column/tabular formatting detected; verify ATS extraction."
        )

    if "\ufffd" in text:
        issues.append("Some characters could not be extracted cleanly.")

    score = 100

    score -= min(25, len(issues) * 7)

    if section_count >= 5:
        score += 5

    score = max(0, min(100, score))

    return {
        "score": score,
        "standard_section_count": section_count,
        "issues": issues,
        "positives": positives,
        "possible_multi_column": possible_columns,
        "note": "ATS compatibility is an estimate based on extracted text and structure; it is not a guarantee of passing a specific ATS.",
    }