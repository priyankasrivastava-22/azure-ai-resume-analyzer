import re
import unicodedata
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SECTION_ALIASES = {
    "summary": [
        "summary",
        "professional summary",
        "profile",
        "career summary",
        "objective",
        "professional profile",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "technical expertise",
        "technologies",
        "technical competencies",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "career history",
    ],
    "education": [
        "education",
        "academic background",
        "academic qualifications",
        "qualifications",
    ],
    "projects": [
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "professional certifications",
    ],
    "achievements": [
        "achievements",
        "accomplishments",
        "awards",
    ],
}


# Repair known and common document-extraction artifacts.
def clean_extraction_artifacts(text):
    if not text:
        return ""

    replacements = {
        r"\bT\s+ata\b": "Tata",
        r"\bc\s+onfiguration\b": "configuration",
        r"\bservicedelays\b": "service delays",
        r"\bdocument\s+ation\b": "documentation",
        r"\bcompl\s+eteness\b": "completeness",
        r"\bprov\s+iding\b": "providing",
        r"\bprov\s+ide\b": "provide",
        r"\bproduc\s+tion\b": "production",
        r"\bconfigur\s+ation\b": "configuration",
        r"\bautomat\s+e\b": "automate",
        r"\banomalydetection\b": "anomaly detection",
        r"\bonevery\b": "on every",
        r"\bS\s+OC2\b": "SOC2",
        r"\bSS\s+AE18\b": "SSAE18",
        r"\bA\s+I\b": "AI",
        r"\bM\s+FA\b": "MFA",
        r"\bR\s+CA\b": "RCA",
        r"\bI\s+a\s+c\b": "IaC",
        r"\bIa\s+c\b": "IaC",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    # Join words split by a hyphen across line breaks.
    text = re.sub(
        r"([A-Za-z])-\s*\n\s*([A-Za-z])",
        r"\1\2",
        text,
    )

    # Remove spaces before punctuation.
    text = re.sub(
        r"\s+([,.;:!?])",
        r"\1",
        text,
    )

    # Normalize spaces around hyphens used inside words.
    text = re.sub(
        r"(?<=\w)\s*-\s*(?=\w)",
        "-",
        text,
    )

    return text


# Normalize extracted document text while preserving useful line boundaries.
def clean_text(text):
    if not text:
        return ""

    # Normalize Unicode representations produced by PDF and DOCX extraction.
    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = clean_extraction_artifacts(text)

    lines = []

    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


# Extract and clean text from a PDF document.
def extract_pdf_text(file_bytes):
    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(
            f"Unable to read PDF file: {exc}"
        ) from exc

    pages = []

    for page in reader.pages:
        page_text = page.extract_text() or ""

        if page_text.strip():
            pages.append(page_text)

    return clean_text(
        "\n".join(pages)
    )


# Extract paragraph and table text from a DOCX document.
def extract_docx_text(file_bytes):
    try:
        document = Document(BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(
            f"Unable to read DOCX file: {exc}"
        ) from exc

    lines = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            lines.append(text)

    for table in document.tables:
        for row in table.rows:
            values = []

            for cell in row.cells:
                value = cell.text.strip()

                if value:
                    values.append(value)

            if values:
                lines.append(
                    " | ".join(values)
                )

    return clean_text(
        "\n".join(lines)
    )


# Route the uploaded file to the correct text extractor.
def extract_text(file_bytes, filename):
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_bytes)

    if extension == ".docx":
        return extract_docx_text(file_bytes)

    if extension == ".txt":
        return clean_text(
            file_bytes.decode(
                "utf-8",
                errors="ignore",
            )
        )

    raise ValueError(
        "Unsupported file type. "
        "Please upload PDF, DOCX, or TXT."
    )


# Normalize a possible section heading for matching.
def normalize_heading(text):
    value = re.sub(
        r"[^a-zA-Z ]",
        "",
        text.lower(),
    ).strip()

    return re.sub(
        r"\s+",
        " ",
        value,
    )


# Map a detected heading to its canonical resume section.
def detect_section_heading(line):
    normalized = normalize_heading(line)

    for section, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section

    return None


# Split resume text into recognized logical sections.
def extract_sections(text):
    sections = {
        "header": [],
    }
    current_section = "header"

    for line in text.splitlines():
        heading = detect_section_heading(line)

        if heading:
            current_section = heading
            sections.setdefault(
                current_section,
                [],
            )
            continue

        sections.setdefault(
            current_section,
            [],
        ).append(line)

    cleaned = {}

    for name, lines in sections.items():
        value = "\n".join(
            line.strip()
            for line in lines
            if line.strip()
        )

        if value:
            cleaned[name] = value

    return cleaned


# Return non-empty normalized lines from extracted text.
def get_lines(text):
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]