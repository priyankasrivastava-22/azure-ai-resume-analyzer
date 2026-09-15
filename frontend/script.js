const uploadArea = document.getElementById("uploadArea");
const resumeFile = document.getElementById("resumeFile");
const fileName = document.getElementById("fileName");
const analyzeBtn = document.getElementById("analyzeBtn");
const loader = document.getElementById("loader");
const errorMessage = document.getElementById("errorMessage");
const results = document.getElementById("results");

let selectedFile = null;

uploadArea.addEventListener("click", () => {
    resumeFile.click();
});

resumeFile.addEventListener("change", () => {
    if (resumeFile.files.length > 0) {
        selectedFile = resumeFile.files[0];

        fileName.textContent = selectedFile.name;
        errorMessage.textContent = "";
        errorMessage.style.display = "none";

        analyzeBtn.disabled = false;
    }
});

uploadArea.addEventListener("dragover", (event) => {
    event.preventDefault();
    uploadArea.classList.add("dragover");
});

uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("dragover");
});

uploadArea.addEventListener("drop", (event) => {
    event.preventDefault();
    uploadArea.classList.remove("dragover");

    if (event.dataTransfer.files.length > 0) {
        selectedFile = event.dataTransfer.files[0];

        fileName.textContent = selectedFile.name;
        errorMessage.textContent = "";
        errorMessage.style.display = "none";

        analyzeBtn.disabled = false;
    }
});

analyzeBtn.addEventListener("click", async () => {
    if (!selectedFile) {
        showError("Please select a PDF or TXT resume.");
        return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    loader.style.display = "block";
    errorMessage.style.display = "none";
    results.style.display = "none";
    analyzeBtn.disabled = true;

    try {
        const response = await fetch("http://localhost:7071/api/analyze", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Resume analysis failed.");
        }

        displayResults(data);

    } catch (error) {
        showError(error.message);

    } finally {
        loader.style.display = "none";
        analyzeBtn.disabled = false;
    }
});

function displayResults(data) {
    const candidate = data.candidate;
    const analysis = data.analysis;

    document.getElementById("candidateName").textContent =
        candidate.name;

    document.getElementById("score").textContent =
        analysis.score;

    document.getElementById("skills").textContent =
        analysis.skills.join(", ");

    document.getElementById("experience").textContent =
        analysis.experience_summary;

    document.getElementById("strengths").innerHTML =
        analysis.strengths
            .map(item => `<li>${item}</li>`)
            .join("");

    document.getElementById("recommendations").innerHTML =
        analysis.recommendations
            .map(item => `<li>${item}</li>`)
            .join("");

    results.style.display = "block";
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = "block";
}