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

CORE_HEADINGS = {
    "summary",
    "skills",
    "experience",
    "education",
}


def analyze_ats(text, sections):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    issues = []
    positives = []

    # Count only standard sections that contain extracted content.
    detected_sections = [
        section
        for section in STANDARD_HEADINGS
        if sections.get(section)
    ]

    section_count = len(detected_sections)

    core_section_count = sum(
        1
        for section in CORE_HEADINGS
        if sections.get(section)
    )

    score = 0

    # Score standard resume structure.
    section_score = min(
        35,
        round((core_section_count / len(CORE_HEADINGS)) * 35),
    )
    score += section_score

    if core_section_count == len(CORE_HEADINGS):
        positives.append("Core ATS-friendly resume sections detected.")
    elif core_section_count >= 3:
        positives.append("Most core resume sections were detected.")
    else:
        issues.append("Several core resume sections are missing.")

    # Score contact information.
    email_detected = bool(
        re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            text,
        )
    )

    if email_detected:
        score += 8
        positives.append("Email address detected.")
    else:
        issues.append("Email address was not detected.")

    phone_detected = bool(
        re.search(
            r"\+?\d[\d\s().-]{8,}\d",
            text,
        )
    )

    if phone_detected:
        score += 7
        positives.append("Phone number detected.")
    else:
        issues.append("Phone number was not detected.")

    # Reward bullet-based experience and achievement formatting.
    bullet_lines = [
        line
        for line in lines
        if re.match(r"^[•●▪◦*-]\s+", line)
    ]

    if bullet_lines:
        score += 10
        positives.append("Bullet-based content detected.")
    else:
        issues.append("No standard bullet structure detected.")

    # Detect repeated content that may reduce resume quality.
    repeated_lines = []
    seen = set()

    for line in lines:
        normalized = re.sub(r"\W", "", line.lower())

        if len(normalized) <= 20:
            continue

        if normalized in seen:
            repeated_lines.append(line)
        else:
            seen.add(normalized)

    if repeated_lines:
        issues.append("Repeated lines were detected.")
    else:
        score += 8

    # Score whether the extracted resume length is reasonable.
    text_length = len(text)

    if text_length < 800:
        issues.append("Resume contains relatively little extracted text.")
    elif text_length > 15000:
        issues.append("Resume may contain excessive content.")
        score += 5
    else:
        score += 15
        positives.append("Resume contains an appropriate amount of text.")

    # Detect possible multi-column or tabular formatting.
    possible_columns = any(
        "\t" in line or re.search(r"\S {5,}\S", line)
        for line in text.splitlines()
    )

    if possible_columns:
        issues.append(
            "Possible multi-column/tabular formatting detected; "
            "verify ATS extraction."
        )
    else:
        score += 10
        positives.append("No obvious multi-column formatting detected.")

    # Detect corrupted characters from document extraction.
    if "\ufffd" in text:
        issues.append("Some characters could not be extracted cleanly.")
    else:
        score += 7
        positives.append("Text extraction appears clean.")

    score = max(0, min(100, round(score)))

    return {
        "score": score,
        "standard_section_count": section_count,
        "issues": issues,
        "positives": positives,
        "possible_multi_column": possible_columns,
        "note": (
            "ATS compatibility is an estimate based on extracted text "
            "and structure; it is not a guarantee of passing a specific ATS."
        ),
    }