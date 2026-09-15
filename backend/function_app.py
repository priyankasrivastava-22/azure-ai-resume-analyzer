import json
import logging
import re
from io import BytesIO

import azure.functions as func
from pypdf import PdfReader

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#",
    "SQL", "PL/SQL", "HTML", "CSS", "React", "Node.js", "Express",
    "FastAPI", "Flask", "Spring", "Spring Boot", "Docker", "Kubernetes",
    "Terraform", "Ansible", "Jenkins", "Git", "GitHub", "GitLab",
    "Azure", "AWS", "GCP", "Linux", "Oracle", "PostgreSQL", "MySQL",
    "MongoDB", "Redis", "REST API", "REST", "CI/CD", "GitHub Actions"
]

def extract_name(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:10]:
        if re.fullmatch(r"[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*){1,3}", line):
            return line
    match = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s+is\s+", text)
    if match:
        return match.group(1)
    return "Not identified"

def extract_skills(text):
    found_skills = []
    for skill in SKILLS:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(skill) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill)
    return found_skills

def extract_experience(text):
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?experience\b", text, re.IGNORECASE)
    if match:
        years = float(match.group(1))
        return f"Approximately {match.group(1)} years of professional experience identified.", years

    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b", text, re.IGNORECASE)
    if match:
        years = float(match.group(1))
        return f"Approximately {match.group(1)} years of experience identified.", years

    experience_section = re.search(
        r"(?:work experience|professional experience|experience)(.*?)(?:education|skills|projects|certifications|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if experience_section:
        section = experience_section.group(1)
        if re.search(
            r"\b(?:developer|engineer|associate|analyst|intern|trainee|manager|consultant)\b",
            section,
            re.IGNORECASE
        ):
            return "Professional work experience is present in the resume.", 1

    return "Professional experience could not be determined from the provided resume.", 0

def extract_education(text):
    education_keywords = [
        "BCA", "MCA", "B.Tech", "BTech", "M.Tech", "MTech",
        "Bachelor", "Master", "B.Sc", "M.Sc", "MBA", "PhD", "Ph.D"
    ]

    found = []

    for keyword in education_keywords:
        pattern = r"(?<![A-Za-z])" + re.escape(keyword) + r"(?![A-Za-z])"
        if re.search(pattern, text, re.IGNORECASE):
            found.append(keyword)

    return list(dict.fromkeys(found))

def extract_pdf_text(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    pages = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages.append(page_text)

    return "\n".join(pages).strip()

def calculate_score(text, skills, experience_years, education):
    score = 0

    score += min(len(skills) * 4, 40)

    if experience_years >= 5:
        score += 25
    elif experience_years >= 3:
        score += 20
    elif experience_years >= 1:
        score += 12
    elif experience_years > 0:
        score += 6

    if education:
        score += 15

    lower_text = text.lower()
    completeness_score = 0

    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
        completeness_score += 3

    if re.search(r"\+?\d[\d\s()-]{8,}\d", text):
        completeness_score += 3

    if "linkedin" in lower_text:
        completeness_score += 2

    if "github" in lower_text:
        completeness_score += 2

    score += min(completeness_score, 10)

    sections = [
        "experience", "education", "skills",
        "project", "projects", "summary"
    ]

    content_score = sum(2 for section in sections if section in lower_text)
    score += min(content_score, 10)

    return min(score, 100)

def generate_strengths(skills, experience_years, education, text):
    strengths = []

    if len(skills) >= 6:
        strengths.append("Strong technical skill coverage")
    elif len(skills) >= 3:
        strengths.append("Good technical skill coverage")

    if experience_years >= 3:
        strengths.append("Relevant professional experience")
    elif experience_years > 0:
        strengths.append("Professional experience is present")

    if education:
        strengths.append("Education information is clearly represented")

    if "project" in text.lower():
        strengths.append("Project experience is included")

    if not strengths:
        strengths.append("Resume contains basic candidate information")

    return strengths

def generate_recommendations(skills, experience_years, education, text):
    recommendations = []
    lower_text = text.lower()

    if len(skills) < 5:
        recommendations.append(
            "Add relevant technical skills and tools used in your work."
        )

    if experience_years == 0:
        recommendations.append(
            "Clearly mention professional experience or relevant project experience."
        )

    if not education:
        recommendations.append(
            "Add your highest relevant educational qualification."
        )

    if not re.search(
        r"\d+%|\d+\+|\d+\s+(users|customers|projects|applications|systems|environments)",
        text,
        re.IGNORECASE
    ):
        recommendations.append(
            "Add measurable achievements such as percentages, volumes, time saved, or number of projects."
        )

    if "github" not in lower_text:
        recommendations.append(
            "Consider adding a GitHub or portfolio link if you have relevant projects."
        )

    if "linkedin" not in lower_text:
        recommendations.append(
            "Consider adding a LinkedIn profile link."
        )

    if not recommendations:
        recommendations.append(
            "Resume has good baseline coverage. Continue tailoring it to each job description."
        )

    return recommendations[:5]

def analyze_resume(text):
    candidate_name = extract_name(text)
    skills = extract_skills(text)
    experience_summary, experience_years = extract_experience(text)
    education = extract_education(text)
    score = calculate_score(text, skills, experience_years, education)
    strengths = generate_strengths(skills, experience_years, education, text)
    recommendations = generate_recommendations(
        skills,
        experience_years,
        education,
        text
    )

    return {
        "candidate": {
            "name": candidate_name
        },
        "analysis": {
            "score": score,
            "skills": skills,
            "experience_summary": experience_summary,
            "experience_years": experience_years,
            "education": education,
            "strengths": strengths,
            "recommendations": recommendations
        }
    }

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({
            "success": True,
            "status": "healthy",
            "service": "AI Resume Analyzer API"
        }),
        mimetype="application/json",
        status_code=200
    )

@app.route(route="analyze", methods=["POST"])
def analyze(req: func.HttpRequest) -> func.HttpResponse:
    try:
        content_type = req.headers.get("Content-Type", "")

        if "multipart/form-data" in content_type:
            files = req.files

            if "file" not in files:
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "error": "No resume file uploaded."
                    }),
                    status_code=400,
                    mimetype="application/json"
                )

            file = files["file"]
            filename = file.filename or ""
            file_bytes = file.stream.read()

            if not file_bytes:
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "error": "Uploaded file is empty."
                    }),
                    status_code=400,
                    mimetype="application/json"
                )

            if len(file_bytes) > 5 * 1024 * 1024:
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "error": "File size must be below 5 MB."
                    }),
                    status_code=400,
                    mimetype="application/json"
                )

            if filename.lower().endswith(".pdf"):
                resume_text = extract_pdf_text(file_bytes)
            elif filename.lower().endswith(".txt"):
                resume_text = file_bytes.decode("utf-8", errors="ignore").strip()
            else:
                return func.HttpResponse(
                    json.dumps({
                        "success": False,
                        "error": "Only PDF and TXT files are supported."
                    }),
                    status_code=400,
                    mimetype="application/json"
                )
        else:
            body = req.get_json()
            resume_text = body.get("resume_text", "").strip()

        if not resume_text:
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": "Resume text could not be extracted."
                }),
                status_code=400,
                mimetype="application/json"
            )

        result = analyze_resume(resume_text)

        return func.HttpResponse(
            json.dumps({
                "success": True,
                **result
            }),
            status_code=200,
            mimetype="application/json"
        )

    except ValueError:
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": "Invalid request."
            }),
            status_code=400,
            mimetype="application/json"
        )

    except Exception as e:
        logging.exception("Resume analysis failed")

        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )