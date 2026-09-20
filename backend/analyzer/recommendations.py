# Generate resume strengths and improvement recommendations.
def generate_resume_recommendations(resume, resume_quality, quality_breakdown, ats):
    recommendations = []
    strengths = []

    # Evaluate resume content completeness.
    if quality_breakdown["content_completeness"] >= 12:
        strengths.append("Resume contains most core sections.")
    else:
        recommendations.append(
            "Add missing core sections such as Summary, Experience, "
            "Skills, Education, or Projects."
        )

    # Evaluate experience quality.
    if quality_breakdown["experience_quality"] >= 15:
        strengths.append(
            "Experience bullets show reasonable action and technical detail."
        )
    else:
        recommendations.append(
            "Rewrite experience bullets with stronger action verbs "
            "and clearer technical ownership."
        )

    # Evaluate measurable achievements.
    if quality_breakdown["achievement_impact"] >= 10:
        strengths.append(
            "Resume includes measurable achievements or outcomes."
        )
    else:
        recommendations.append(
            "Add measurable outcomes such as time saved, incidents reduced, "
            "deployment frequency, performance improvement, or scale."
        )

    # Evaluate technical skill coverage.
    if quality_breakdown["skills"] >= 10:
        strengths.append(
            "Technical skills are reasonably well represented."
        )
    else:
        recommendations.append(
            "Create a clearer technical skills section grouped by category."
        )

    # Evaluate ATS readability.
    if ats["score"] >= 85:
        strengths.append(
            "Resume structure appears reasonably ATS-readable."
        )
    else:
        recommendations.append(
            "Use standard section headings and verify that the resume "
            "extracts in the correct reading order."
        )

    # Check contact information.
    if not resume.get("email"):
        recommendations.append("Add a professional email address.")

    if not resume.get("phone"):
        recommendations.append("Add a reachable phone number.")

    # Flag excessive use of weak action verbs.
    if resume.get("experience_quality", {}).get("weak_verb_ratio", 0) >= 25:
        recommendations.append(
            "Reduce phrases such as 'worked on', 'responsible for', and "
            "'helped with'; describe the action and outcome instead."
        )

    return strengths, recommendations


# Generate recommendations based on resume-to-JD matching results.
def generate_jd_recommendations(resume, jd, jd_match):
    recommendations = []

    # Report critical missing skills.
    critical_missing = jd_match.get("critical_missing_skills", [])

    if critical_missing:
        recommendations.append(
            "Critical requirement gaps: "
            + ", ".join(critical_missing)
            + ". Add these only if you genuinely have the experience."
        )

    # Report missing general requirements.
    general = jd_match.get("general_requirements", {})
    required_general_missing = general.get("required_missing", [])

    if required_general_missing:
        recommendations.append(
            "Required JD areas not clearly evidenced: "
            + ", ".join(required_general_missing)
            + ". Highlight relevant experience where accurate."
        )

    # Report experience gaps.
    experience = jd_match.get("experience_match", {})

    if (
        experience.get("required_years") is not None
        and experience.get("resume_years") is not None
        and experience["resume_years"] < experience["required_years"]
    ):
        recommendations.append(
            f"The JD asks for {experience['required_years']:g}+ years, "
            f"while approximately {experience['resume_years']:g} years "
            "were identified. Do not inflate the number; emphasize the "
            "most relevant professional experience."
        )

    # Report preferred skill gaps.
    preferred_missing = jd_match.get("preferred_missing_skills", [])

    if preferred_missing:
        recommendations.append(
            "Preferred skills not identified: "
            + ", ".join(preferred_missing)
            + ". These are lower priority than required gaps."
        )

    # Report alternative requirement status.
    alternative_groups = jd_match.get("alternative_requirements", [])

    for group in alternative_groups:
        options = group.get("options", [])
        label = group.get("label")

        if not label:
            if options:
                label = (
                    "Alternative requirement ("
                    + " / ".join(options)
                    + ")"
                )
            else:
                label = "Alternative requirement"

        if group.get("satisfied"):
            matched = ", ".join(group.get("matched", []))

            recommendations.append(
                f"{label}: requirement satisfied through {matched}; "
                "other options are not mandatory."
            )
        else:
            recommendations.append(
                f"{label}: none of the accepted alternatives were identified."
            )

    # Report role alignment issues only when a role score is measurable.
    role_score = jd_match.get("role_match", {}).get("score")
    if role_score is not None and role_score < 70:
        recommendations.append(
            "The resume's role positioning could be closer to the target role. "
            "Use the job's terminology where it truthfully reflects your experience."
        )

    # Report responsibility alignment issues only when a score is measurable.
    keyword_score = jd_match.get("keyword_match")
    if keyword_score is not None and keyword_score < 70:
        recommendations.append(
            "Several JD responsibilities are not clearly reflected in the resume. "
            "Add relevant responsibilities using the employer's terminology "
            "where accurate."
        )

    # Return a positive message when no gaps were identified.
    if not recommendations:
        recommendations.append(
            "The resume has strong alignment with the selected job description. "
            "Focus on evidence and measurable outcomes rather than adding "
            "unrelated keywords."
        )

    return recommendations