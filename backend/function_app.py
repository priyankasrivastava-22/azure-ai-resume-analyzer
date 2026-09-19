import json
import logging
from pathlib import Path

import azure.functions as func

from analyzer.ats_analyzer import analyze_ats
from analyzer.azure_language import analyze_text_with_azure
from analyzer.cosmos_storage import build_analysis_document, save_analysis
from analyzer.jd_analyzer import analyze_jd
from analyzer.parser import extract_sections, extract_text
from analyzer.recommendations import generate_jd_recommendations, generate_resume_recommendations
from analyzer.resume_analyzer import analyze_resume
from analyzer.scoring import calculate_jd_match, calculate_resume_quality


MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MIN_JOB_DESCRIPTION_LENGTH = 100
ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".txt"}

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# Return a consistent JSON HTTP response.
def json_response(data: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        mimetype="application/json",
        status_code=status_code,
    )

# Return a consistent API error response.
def error_response(code: str, message: str, status_code: int) -> func.HttpResponse:
    return json_response(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
        status_code=status_code,
    )

# Check whether the Azure Function API is running.
@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return json_response(
        {
            "success": True,
            "service": "AI Resume Analyzer",
            "status": "healthy",
        }
    )


# Read resume and job-description data from multipart or JSON requests.
def get_request_data(req: func.HttpRequest) -> tuple[str, bytes, str]:
    content_type = req.headers.get("content-type", "").lower()

    # Handle file uploads from the frontend.
    if "multipart/form-data" in content_type:
        uploaded_file = req.files.get("file")

        if uploaded_file is None:
            raise ValueError("Resume file is required.")

        filename = uploaded_file.filename or ""
        file_bytes = uploaded_file.read()
        job_description = (
            req.form.get("job_description")
            or req.form.get("jobDescription")
            or ""
        )

        return filename, file_bytes, job_description

    # Handle JSON requests used for local API testing.
    try:
       body = req.get_json() or {}
    except ValueError as exc:
       raise ValueError("Invalid JSON request body.") from exc

    if not isinstance(body, dict):
      raise ValueError("JSON request body must be an object.")

    filename = body.get("filename", "resume.txt")
    resume_text = body.get("resume_text", "")
    job_description = (
        body.get("job_description")
        or body.get("jobDescription")
        or ""
    )

    if not isinstance(resume_text, str):
        raise ValueError("Resume text must be a string.")

    if not isinstance(job_description, str):
        raise ValueError("Job description must be a string.")

    return filename, resume_text.encode("utf-8"), job_description


# Validate uploaded resume data and job-description input.
def validate_request(filename: str, file_bytes: bytes, job_description: str) -> None:
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("Resume filename is required.")

    if not isinstance(file_bytes, bytes) or not file_bytes:
        raise ValueError("Resume file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError("Resume file is too large. Maximum size is 5 MB.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_FILE_EXTENSIONS:
        raise ValueError("Unsupported resume file type. Allowed types are PDF, DOCX, and TXT.")

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("Job description is required.")

    if len(job_description.strip()) < MIN_JOB_DESCRIPTION_LENGTH:
        raise ValueError("Job description is too short for reliable matching. Please provide the complete job description.")


# Run Azure NLP without allowing a cloud-service failure to stop core analysis.
def safe_azure_analysis(text: str) -> dict:
    try:
        result = analyze_text_with_azure(text)
        return {
            "available": True,
            **result,
        }
    except Exception:
        logging.exception("Azure AI Language analysis failed.")

        return {
            "available": False,
            "key_phrases": [],
            "entities": [],
        }

# Save analysis history without allowing Cosmos errors to break analysis.
def safe_save_analysis(filename, resume, resume_quality, ats, jd, jd_match, recommendations):
    try:
        document = build_analysis_document(filename, resume, resume_quality, ats, jd, jd_match, recommendations)
        return save_analysis(document)
    except Exception:
        logging.exception("Cosmos DB analysis save failed.")
        return None

# Analyze the uploaded resume against the supplied job description.
@app.route(route="analyze", methods=["POST"])
def analyze(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Read and validate the incoming request.
        filename, file_bytes, job_description = get_request_data(req)
        validate_request(filename, file_bytes, job_description)

        # Extract readable text and logical sections from the resume.
        resume_text = extract_text(file_bytes, filename)

        if not resume_text.strip():
            raise ValueError(
                "No readable text was extracted from the resume. "
                "If this is a scanned PDF, OCR support will be required."
            )

        sections = extract_sections(resume_text)

        # Run deterministic resume analysis.
        resume = analyze_resume(resume_text, sections)

        # Enrich resume text with Azure AI Language.
        resume_azure = safe_azure_analysis(resume_text)

        # Evaluate ATS-related resume quality.
        ats = analyze_ats(resume_text, sections)
        quality_result = calculate_resume_quality(resume, ats, sections)
        resume_quality = quality_result["score"]
        quality_breakdown = quality_result["breakdown"]

        # Generate resume strengths and improvement recommendations.
        ( resume_strengths, resume_recommendations) = generate_resume_recommendations( resume, resume_quality, quality_breakdown, ats)

        # Analyze the job description using deterministic rules.
        jd = analyze_jd(job_description)

        # Enrich the job description with Azure AI Language.
        jd_azure = safe_azure_analysis(job_description)

        # Calculate deterministic resume-to-job matching.
        jd_match = calculate_jd_match(resume, resume_text, jd)

        # Generate recommendations based on missing job requirements.
        jd_recommendations = generate_jd_recommendations(resume, jd, jd_match)

        # Save the completed analysis and capture its persistent ID.
        saved_analysis = safe_save_analysis(filename, resume, resume_quality, ats, jd, jd_match, jd_recommendations)
        analysis_id = saved_analysis.get("id") if saved_analysis else None

        # Build the final API response.
        response = {
            "success": True,
            "analysis_id": analysis_id,
            "candidate": {"name": resume.get("name")},
            "analysis": {
                "resume_score": resume_quality,
                "quality_breakdown": quality_breakdown,
                "skills": resume.get("skills", []),
                "experience_summary": resume.get("experience_summary"),
                "experience_years": resume.get("experience_years"),
                "education": resume.get("education", []),
                "sections": sections,
                "contact": {"email": resume.get("email"), "phone": resume.get("phone")},
                "roles": resume.get("roles", []),
                "experience_quality": resume.get("experience_quality", {}),
                "strengths": resume_strengths,
                "recommendations": resume_recommendations,
                "ats": ats,
            },
            "job_match": {
                "match_score": jd_match["match_score"],
                "breakdown": jd_match["breakdown"],
                "required_skill_breakdown": jd_match.get("required_skill_breakdown", {}),
                "preferred_skill_breakdown": jd_match.get("preferred_skill_breakdown", {}),
                "jd_skills": jd.get("skills", []),
                "matched_skills": jd_match["matched_skills"],
                "missing_skills": jd_match["missing_skills"],
                "critical_missing_skills": jd_match["critical_missing_skills"],
                "preferred_missing_skills": jd_match["preferred_missing_skills"],
                "experience_match": jd_match["experience_match"],
                "role_match": jd_match["role_match"],
                "keyword_match": jd_match["keyword_match"],
                "keyword_match_details": jd_match.get("keyword_match_details", {}),
                "education_match": jd_match["education_match"],
                "general_requirements": jd_match["general_requirements"],
                "alternative_requirements": jd_match["alternative_requirements"],
                "score_explanations": jd_match.get("score_explanations", {}),
                "recommendations": jd_recommendations,
                },
            "azure_ai": {
                "resume": resume_azure, 
                "job_description": jd_azure,
                },
        }

        return json_response(response)

    except ValueError as exc:
        logging.warning("Validation error: %s", exc)

        return error_response("VALIDATION_ERROR", str(exc), 400)

    except Exception:
        logging.exception("Resume analysis failed.")

    return error_response("INTERNAL_ERROR", "Resume analysis failed.", 500)