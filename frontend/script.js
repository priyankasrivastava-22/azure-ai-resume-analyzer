const resumeFile = document.getElementById("resumeFile");
const fileName = document.getElementById("fileName");
const jobDescription = document.getElementById("jobDescription");
const analyzeBtn = document.getElementById("analyzeBtn");
const loader = document.getElementById("loader");
const errorMessage = document.getElementById("errorMessage");
const results = document.getElementById("results");

const MAX_NLP_PHRASES = 10;
const MAX_NLP_ENTITIES = 10;

resumeFile.addEventListener("change", handleFileSelection);
jobDescription.addEventListener("input", updateButtonState);
analyzeBtn.addEventListener("click", analyzeResume);

function handleFileSelection() {
    fileName.textContent = resumeFile.files.length ? resumeFile.files[0].name : "";
    updateButtonState();
}

function updateButtonState() {
    const hasFile = resumeFile.files.length > 0;
    const hasJobDescription = jobDescription.value.trim().length >= 100;
    analyzeBtn.disabled = !(hasFile && hasJobDescription);
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}

function hideError() {
    errorMessage.textContent = "";
    errorMessage.classList.add("hidden");
}

// Toggle the interface while analysis is running.
function setLoading(isLoading) {
    loader.classList.toggle("hidden", !isLoading);
    analyzeBtn.disabled = isLoading;
    resumeFile.disabled = isLoading;
    jobDescription.disabled = isLoading;
    analyzeBtn.textContent = isLoading ? "Analyzing..." : "Analyze Resume";

    if (!isLoading) {
        updateButtonState();
    }
}

function createSkillTags(container, items = []) {
    if (!container) return;

    container.innerHTML = "";

    if (!items.length) {
        container.textContent = "None detected";
        return;
    }

    items.forEach(item => {
        const tag = document.createElement("span");
        tag.className = "skill-tag";
        tag.textContent = item;
        container.appendChild(tag);
    });
}

function createList(container, items = []) {
    if (!container) return;

    container.innerHTML = "";

    if (!items.length) {
        const item = document.createElement("li");
        item.textContent = "None";
        container.appendChild(item);
        return;
    }

    items.forEach(value => {
        const item = document.createElement("li");
        item.textContent = value;
        container.appendChild(item);
    });
}

function normalizePhrase(value) {
    return String(value || "")
        .toLowerCase()
        .replace(/[^\w+#./ -]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function cleanPhrases(phrases = [], limit = MAX_NLP_PHRASES) {
    const seen = new Set();
    const cleaned = [];

    for (const phrase of phrases) {
        const value = String(phrase || "").trim();
        const normalized = normalizePhrase(value);

        if (!normalized || normalized.length < 3 || normalized.length > 80) {
            continue;
        }

        if (seen.has(normalized)) {
            continue;
        }

        seen.add(normalized);
        cleaned.push(value);

        if (cleaned.length >= limit) {
            break;
        }
    }

    return cleaned;
}

function cleanEntities(entities = []) {
    const seen = new Set();
    const cleaned = [];

    for (const entity of entities) {
        const value =
            typeof entity === "string"
                ? entity
                : entity?.text || entity?.name || "";

        const normalized = normalizePhrase(value);

        if (
            !normalized ||
            normalized.length < 2 ||
            normalized.length > 60 ||
            value.includes("@") ||
            /^\+?\d[\d\s()-]{6,}$/.test(value.trim()) ||
            /^\d+(?:\.\d+)?$/.test(value.trim())
        ) {
            continue;
        }

        if (seen.has(normalized)) {
            continue;
        }

        seen.add(normalized);
        cleaned.push(value.trim());

        if (cleaned.length >= MAX_NLP_ENTITIES) {
            break;
        }
    }

    return cleaned;
}

// Send resume and job description to the analyzer API.
async function analyzeResume() {
    hideError();

    const file = resumeFile.files[0];
    const jd = jobDescription.value.trim();

    if (!file) {
        showError("Please upload a resume.");
        return;
    }

    if (jd.length < 100) {
        showError("Please provide a complete job description of at least 100 characters.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("job_description", jd);

    setLoading(true);
    results.classList.add("hidden");

    try {
        let response;

        try {
            response = await fetch("https://ai-resume-analyzer-api-ps.azurewebsites.net/api/analyze", {
                method: "POST",
                body: formData,
            });
        } catch {
            throw new Error("Unable to connect to the analyzer service. Please try again.");
        }

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error("The analyzer returned an invalid response.");
        }

        if (!response.ok || !data.success) {
            throw new Error(data.error?.message || "Unable to analyze the resume.");
        }

        displayResults(data);
    } catch (error) {
        showError(error.message || "Resume analysis failed. Please try again.");
    } finally {
        setLoading(false);
    }
}

// Render deterministic analysis and supplemental Azure NLP insights.
function displayResults(data) {
    const analysis = data.analysis || {};
    const jobMatch = data.job_match || {};
    const azureResume = data.azure_ai?.resume;
    const azureJob = data.azure_ai?.job_description;

    document.getElementById("resumeScore").textContent =
        analysis.resume_score ?? "N/A";

    document.getElementById("atsScore").textContent =
        analysis.ats?.score ?? "N/A";

    document.getElementById("jdMatchScore").textContent =
        jobMatch.match_score ?? "N/A";

    document.getElementById("candidateName").textContent =
        data.candidate?.name || "Not detected";

    createSkillTags(
        document.getElementById("matchedSkills"),
        jobMatch.matched_skills || []
    );

    createSkillTags(
        document.getElementById("missingSkills"),
        jobMatch.missing_skills || []
    );

    createSkillTags(
        document.getElementById("skills"),
        analysis.skills || []
    );

    document.getElementById("experienceMatch").textContent =
        jobMatch.experience_match?.status || "Not available";

    document.getElementById("roleMatch").textContent =
        jobMatch.role_match?.status || "Not available";

    document.getElementById("keywordMatch").textContent =
        jobMatch.keyword_match != null
            ? `${jobMatch.keyword_match}%`
            : "Not available";

    document.getElementById("educationMatch").textContent =
        jobMatch.education_match != null
            ? `${jobMatch.education_match}%`
            : "Not available";

    document.getElementById("experience").textContent =
        analysis.experience_summary || "Not available";

    createList(
        document.getElementById("strengths"),
        analysis.strengths || []
    );

    createList(
        document.getElementById("recommendations"),
        analysis.recommendations || []
    );

    createList(
        document.getElementById("jobRecommendations"),
        jobMatch.recommendations || []
    );

    const resumePhrases = azureResume?.available
        ? cleanPhrases(azureResume.key_phrases)
        : [];

    const jdPhrases = azureJob?.available
        ? cleanPhrases(azureJob.key_phrases)
        : [];

    createSkillTags(
        document.getElementById("resumeKeyPhrases"),
        resumePhrases
    );

    createSkillTags(
        document.getElementById("jdKeyPhrases"),
        jdPhrases
    );

    const resumeEntities = azureResume?.available
        ? cleanEntities(azureResume.entities)
        : [];

    createList(
        document.getElementById("resumeEntities"),
        resumeEntities
    );

    results.classList.remove("hidden");
}