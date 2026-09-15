const fileInput = document.getElementById("resumeFile");
const dropZone = document.getElementById("dropZone");
const fileName = document.getElementById("fileName");
const analyzeButton = document.getElementById("analyzeButton");

const loading = document.getElementById("loading");
const errorMessage = document.getElementById("errorMessage");
const resultsSection = document.getElementById("resultsSection");

let selectedFile = null;


// File selection
fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) {
        handleFile(fileInput.files[0]);
    }
});


// Drag and drop
dropZone.addEventListener("dragover", function (event) {
    event.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", function () {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", function (event) {
    event.preventDefault();

    dropZone.classList.remove("dragover");

    if (event.dataTransfer.files.length > 0) {
        handleFile(event.dataTransfer.files[0]);
    }
});


// Validate selected file
function handleFile(file) {

    const allowedTypes = [
        "application/pdf",
        "text/plain"
    ];

    const maxSize = 5 * 1024 * 1024;

    errorMessage.classList.add("hidden");

    if (!allowedTypes.includes(file.type)) {
        showError("Please upload a PDF or TXT file.");
        return;
    }

    if (file.size > maxSize) {
        showError("File size must be less than 5 MB.");
        return;
    }

    selectedFile = file;

    fileName.textContent = file.name;

    analyzeButton.disabled = false;
}


// Analyze button
analyzeButton.addEventListener("click", async function () {

    if (!selectedFile) {
        showError("Please select a resume first.");
        return;
    }

    loading.classList.remove("hidden");
    errorMessage.classList.add("hidden");
    resultsSection.classList.add("hidden");

    try {

        const text = await extractText(selectedFile);

        if (!text.trim()) {
            throw new Error("Could not extract text from the resume.");
        }

        // Backend will be connected here later.
        console.log("Extracted resume text:", text);

        showError(
            "Frontend is ready. Backend API will be connected next."
        );

    } catch (error) {

        showError(error.message);

    } finally {

        loading.classList.add("hidden");

    }
});


// Extract text from TXT files
async function extractText(file) {

    if (file.type === "text/plain") {
        return await file.text();
    }

    // PDF extraction will be handled by the backend.
    return "PDF file selected. Backend PDF extraction will process this file.";
}


// Display error
function showError(message) {

    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");

}