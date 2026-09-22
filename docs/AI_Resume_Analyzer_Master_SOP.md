# AI Resume Analyzer — Master Standard Operating Procedure (SOP)

**Document type:** Build, test, deploy, secure, and operate SOP  
**Project:** Azure AI Resume Analyzer  
**Repository:** `azure-ai-resume-analyzer`  
**Primary platform:** Microsoft Azure  
**Primary backend runtime:** Python 3.10 / Azure Functions  
**Frontend:** HTML, CSS, JavaScript / Azure Static Web Apps  
**Database:** Azure Cosmos DB for NoSQL  
**AI/NLP service:** Azure AI Language  
**CI/CD:** GitHub Actions with Azure OIDC  
**Audience:** Developers, reviewers, recruiters, and future maintainers  
**Security rule:** Never copy real credentials, API keys, access tokens, connection strings, PATs, or deployment tokens into this SOP.

> **Source note:** Phases 2–9 were consolidated from the project’s phase SOPs. Phase 1 is reconstructed from the baseline architecture documented at the start of Phases 2 and 3 because a separate Phase 1 SOP was not supplied. Phase 10 includes completed secret/.gitignore review steps plus the final hardening procedure that should be executed before the repository is treated as fully production-clean.

---

## 1. Purpose

This SOP provides a repeatable procedure to build and operate the Azure AI Resume Analyzer from local development through automated cloud deployment.

The application accepts a resume and a job description, analyzes both using a deterministic rule-based engine, adds Azure AI Language NLP enrichment, stores analysis history in Cosmos DB, displays the results through a browser UI, and deploys the backend automatically through GitHub Actions.

The final architecture is:

```text
User Browser
    |
    v
Azure Static Web Apps
    |
    v
Azure Functions REST API
    |
    +-------------------------------+
    |                               |
    v                               v
Deterministic Analyzer       Azure AI Language
    |                        (key phrases / NER)
    +---------------+---------------+
                    |
                    v
               Scoring Layer
                    |
                    v
             Recommendations
                    |
                    v
              Azure Cosmos DB
                    |
                    v
          Structured JSON Response
                    |
                    v
             Frontend Dashboard
```

The CI/CD path is:

```text
Developer
   |
   v
git push origin main
   |
   v
GitHub Actions
   |
   v
Syntax checks + pytest
   |
   +---- failure ----> stop; do not deploy
   |
   v
GitHub OIDC
   |
   v
Azure RBAC / Managed Identity
   |
   v
Azure Functions deployment
```

---

## 2. Scope

This SOP covers:

- Local Python environment setup.
- Core analyzer structure.
- Azure AI Language integration.
- Analyzer calibration and explainability.
- Cosmos DB persistence.
- Azure Functions API finalization.
- Frontend integration.
- Automated testing.
- Azure backend/frontend deployment.
- CORS.
- Production environment variables.
- GitHub Actions CI/CD.
- OIDC authentication and RBAC.
- Secret-history checks.
- `.gitignore` review.
- File upload validation and input hardening.
- Error-handling review.
- Safe documentation and screenshot publishing.

This SOP intentionally does **not** publish real credentials.

---

## 3. Credential and Privacy Rules

Before doing any work, follow these rules.

1. Never hard-code Azure keys, Cosmos keys, deployment tokens, PATs, connection strings, or access tokens.
2. Local credentials belong in `.env` or Azure Functions `local.settings.json`, both ignored by Git.
3. Production runtime credentials belong in Azure Function App settings.
4. GitHub deployment authentication should use OIDC, not a long-lived Azure client secret.
5. Do not upload screenshots of Azure “Keys and Endpoint” pages to a public repository.
6. Do not store raw resume file bytes in Cosmos DB.
7. Do not put real subscription, tenant, client, principal, or secret values into a public SOP.
8. In documentation, use placeholders such as:

```text
<AZURE_SUBSCRIPTION_ID>
<AZURE_TENANT_ID>
<AZURE_CLIENT_ID>
<AZURE_LANGUAGE_KEY>
<COSMOS_KEY>
<SWA_DEPLOYMENT_TOKEN>
<GITHUB_PAT>
```

9. Resource names are not credentials, but a reusable SOP should still prefer variables/placeholders where practical.
10. If a secret is ever committed, remove it from Git history **and rotate the secret immediately**.

---

## 4. Reference Resource Names

The project used names similar to the following. Change them if they are unavailable.

```powershell
$RESOURCE_GROUP = "rg-resume-analyzer"
$FUNCTION_APP = "ai-resume-analyzer-api-ps"
$STATIC_WEB_APP = "ai-resume-analyzer-ui-ps"
$COSMOS_ACCOUNT = "ai-resume-analyzer-cosmos-ps"
$COSMOS_DATABASE = "resume-analyzer-db"
$COSMOS_CONTAINER = "analyses"
$LOCATION = "eastus"
$STATIC_LOCATION = "eastus2"

# Storage account names must be globally unique, 3–24 chars, lowercase/alphanumeric.
$STORAGE_NAME = "<globally-unique-storage-name>"
```

Do not hard-code subscription/tenant/client IDs in documentation.

---

## 5. Prerequisites

Install and verify the following:

- Git.
- Python 3.10.x.
- PowerShell.
- Azure CLI.
- Azure Functions Core Tools v4.
- Node.js + npm/npx (needed for Static Web Apps CLI).
- VS Code or another editor.
- GitHub account.
- Azure subscription.

Verify:

```powershell
git --version
python --version
az version
func --version
node --version
npm --version
```

Log in to Azure when needed:

```powershell
az login
az account show --output table
```

---

## 6. Recommended Repository Structure

```text
azure-ai-resume-analyzer/
|
├── .github/
│   └── workflows/
│       └── ci-cd.yml
|
├── backend/
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── ats_analyzer.py
│   │   ├── azure_language.py
│   │   ├── cosmos_storage.py
│   │   ├── jd_analyzer.py
│   │   ├── parser.py
│   │   ├── recommendations.py
│   │   ├── resume_analyzer.py
│   │   └── scoring.py
│   |
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   ├── test_ats_analyzer.py
│   │   ├── test_azure_language.py
│   │   ├── test_experience_matching.py
│   │   ├── test_jd_analyzer.py
│   │   ├── test_recommendations.py
│   │   ├── test_regression_generalized.py
│   │   ├── test_resume_analyzer.py
│   │   └── test_skill_matching.py
│   |
│   ├── function_app.py
│   ├── host.json
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── setup_cosmos.py
|
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
|
├── docs/
│   ├── SOP.md
│   ├── architecture.md
│   └── final-screenshots/
|
├── .env                  # local only; never commit
├── .gitignore
└── README.md
```

---

# PHASE 1 — CORE ANALYZER BASELINE

## 7. Phase 1 Objective

Build a deterministic resume/JD analyzer before adding cloud AI. Later phases explicitly preserved this rule-based engine and used Azure AI Language only as an enrichment layer.

The baseline flow is:

```text
Resume
  |
  v
parser.py
  |
  v
resume_analyzer.py
  |
  +------> ats_analyzer.py
  |
Job Description
  |
  v
jd_analyzer.py
  |
  v
scoring.py
  |
  v
recommendations.py
  |
  v
function_app.py
```

### 7.1 Create or clone the repository

If cloning the finished project:

```powershell
git clone https://github.com/<GITHUB_USER>/azure-ai-resume-analyzer.git
cd azure-ai-resume-analyzer
```

If creating from an empty directory:

```powershell
New-Item -ItemType Directory -Force "azure-ai-resume-analyzer"
Set-Location "azure-ai-resume-analyzer"

git init
```

### 7.2 Create the virtual environment

```powershell
py -3.10 -m venv .venv
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify:

```powershell
python --version
python -m pip --version
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

### 7.3 Create directories

```powershell
New-Item -ItemType Directory -Force backend
New-Item -ItemType Directory -Force backend\analyzer
New-Item -ItemType Directory -Force frontend
New-Item -ItemType Directory -Force docs
```

Create package marker:

```powershell
New-Item -ItemType File -Force backend\analyzer\__init__.py
```

### 7.4 Install baseline dependencies

The Phase 2 starting state documented these baseline runtime packages:

```powershell
python -m pip install azure-functions pypdf
```

Later DOCX support requires:

```powershell
python -m pip install python-docx
```

Record runtime dependencies in:

```text
backend/requirements.txt
```

At minimum, by the end of later phases it includes the project runtime packages such as:

```text
azure-functions
pypdf
python-docx
python-dotenv
azure-ai-textanalytics
azure-cosmos
```

Use actual pinned versions from the repository when reproducibility is required.

### 7.5 Implement module responsibilities

The final codebase separates concerns:

- `parser.py`: extract PDF/DOCX/TXT text and identify sections.
- `resume_analyzer.py`: extract resume evidence such as contact information, experience, skills, and general resume signals.
- `ats_analyzer.py`: calculate ATS compatibility independent of a specific JD.
- `jd_analyzer.py`: extract required/preferred skills, experience, education, responsibilities, alternatives, and general requirements.
- `scoring.py`: calculate resume quality and JD match.
- `recommendations.py`: generate truthful resume and JD-specific recommendations.
- `function_app.py`: orchestrate request parsing, validation, analyzer calls, Azure enrichment, persistence, and the API response.

The architecture rule is:

```text
deterministic evidence first
+
managed AI enrichment second
```

Do not let Azure NER or key phrases directly create skill claims.

### 7.6 Create Azure Functions entry point

The application ultimately exposes:

```text
GET  /api/health
POST /api/analyze
```

Run the host from `backend/`, not the repository root:

```powershell
cd backend
func start
```

Expected routes:

```text
http://localhost:7071/api/health
http://localhost:7071/api/analyze
```

If Core Tools cannot determine the language, confirm `host.json` and `function_app.py` are in the current directory.

### 7.7 Baseline Git hygiene

Create `.gitignore` early. At minimum:

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.env
.env.*
local.settings.json
.vscode/
*.log
.pytest_cache/
.coverage
```

Verify secret files are ignored:

```powershell
git check-ignore -v .env
git check-ignore -v backend/local.settings.json
```

---

# PHASE 2 — AZURE AI LANGUAGE INTEGRATION

## 8. Phase 2 Objective

Add Azure AI Language as a supplementary NLP layer without replacing deterministic matching.

Azure is used for:

- key phrase extraction;
- named entity recognition (NER);
- additional contextual visibility.

Azure AI output does **not** directly decide the JD Match score.

## 8.1 Create Azure AI Language resource

Using Azure Portal:

```text
Azure Portal
→ Create resource
→ Azure AI Language
→ Pricing tier: F0 (Free), if available
→ Create
```

After creation, open:

```text
Resource
→ Keys and Endpoint
```

Use one endpoint and one key locally, but do not copy the real values into source code or documentation.

## 8.2 Create `.env`

From repository root:

```powershell
New-Item .env -ItemType File
code .env
```

Use placeholders:

```dotenv
AZURE_LANGUAGE_ENDPOINT=<your-language-endpoint>
AZURE_LANGUAGE_KEY=<your-language-key>
```

Verify `.env` is ignored:

```powershell
git check-ignore -v .env
git status --short
```

`.env` should not appear as an untracked file.

## 8.3 Install `python-dotenv`

Use the active interpreter’s pip:

```powershell
python -m pip install python-dotenv
python -m pip show python-dotenv
```

Why `python -m pip`: it reduces the risk of installing into the wrong Python interpreter.

## 8.4 Verify credentials without printing them

```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Endpoint loaded:', bool(os.getenv('AZURE_LANGUAGE_ENDPOINT'))); print('Key loaded:', bool(os.getenv('AZURE_LANGUAGE_KEY')))"
```

Expected:

```text
Endpoint loaded: True
Key loaded: True
```

Never print the actual key.

## 8.5 Install Azure AI Language SDK

```powershell
python -m pip install azure-ai-textanalytics
python -m pip show azure-ai-textanalytics
```

Concept:

```text
Azure AI Language = cloud service
azure-ai-textanalytics = Python SDK
```

## 8.6 Create standalone connectivity test

Create:

```text
backend/test_azure_language.py
```

The test should:

1. load `.env`;
2. read endpoint/key;
3. create `TextAnalyticsClient`;
4. send sample resume-style text;
5. call key phrase extraction;
6. confirm a valid response.

Run:

```powershell
python backend/test_azure_language.py
```

This isolates Azure authentication/network problems from analyzer logic.

## 8.7 Create reusable module

Create:

```text
backend/analyzer/azure_language.py
```

The module should expose:

```text
get_azure_language_client()
chunk_text()
extract_key_phrases()
recognize_entities()
analyze_text_with_azure()
```

### Client pattern

Use environment variables:

```python
endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
key = os.getenv("AZURE_LANGUAGE_KEY")
```

Create the client using:

```python
TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key),
)
```

### Key phrase extraction

Conceptually:

```python
client.extract_key_phrases([text])
```

### Named entity recognition

Convert SDK entity objects into normal JSON-safe dictionaries containing only fields required by the API, such as text/category/subcategory/confidence.

### Long text handling

Chunk long resume/JD text before sending it to Azure and merge the output.

### Deduplication

Normalize and deduplicate key phrases before returning them.

## 8.8 Safe Azure failure behavior

Azure AI Language is supplemental. If the external service fails:

```text
deterministic analysis should still succeed
```

Return an `available = false`-style result or equivalent safe structure instead of crashing the core analyzer.

## 8.9 Integrate at orchestration layer

Import into:

```text
backend/function_app.py
```

Example:

```python
from analyzer.azure_language import analyze_text_with_azure
```

Conceptually:

```text
resume_text
├── deterministic resume analysis
└── Azure NLP

job_description
├── deterministic JD analysis
└── Azure NLP
```

Then return Azure results separately:

```json
{
  "azure_ai": {
    "resume": {},
    "job_description": {}
  }
}
```

Do not put Azure NLP directly inside `scoring.py`.

## 8.10 Update dependencies

Update:

```text
backend/requirements.txt
```

Relevant dependencies after Phase 2 include:

```text
azure-functions
pypdf
python-dotenv
azure-ai-textanalytics
```

## 8.11 Phase 2 troubleshooting

### Problem: `pip` not recognized

Use:

```powershell
python -m pip ...
```

### Problem: `python-dotenv` missing

Install:

```powershell
python -m pip install python-dotenv
```

### Problem: `ModuleNotFoundError: analyzer`

Run analyzer imports from the correct backend context:

```powershell
cd backend
python -c "from analyzer.azure_language import analyze_text_with_azure; print('import ok')"
```

### Problem: API returns HTTP 500 after Azure integration

Debug the Azure module independently first, then test the Function route. Keep Azure failures isolated so the deterministic result still works.

### Problem: PowerShell hides nested objects

Use:

```powershell
$response | ConvertTo-Json -Depth 20
```

---

# PHASE 3 — ANALYZER QUALITY, CALIBRATION, EXPLAINABILITY, GENERALIZATION

## 9. Phase 3 Objective

Improve scoring credibility, parser robustness, recommendation quality, and explainability before adding more cloud infrastructure.

## 9.1 Calibrate ATS compatibility

File:

```text
backend/analyzer/ats_analyzer.py
```

The earlier design started at 100 and deducted only limited points, allowing weak resumes to score too highly.

The improved design is additive:

```text
start at 0
→ award points for ATS-positive characteristics
→ cap at 100
```

Signals include:

- core section completeness;
- email;
- phone;
- bullet structure;
- repeated-content checks;
- reasonable length;
- ATS-safe layout;
- clean extracted text.

Syntax test:

```powershell
cd backend
python -m py_compile analyzer/ats_analyzer.py
```

Import test:

```powershell
python -c "from analyzer.ats_analyzer import analyze_ats; print('ATS analyzer imported successfully')"
```

Weak-resume calibration test:

```powershell
python -c "from analyzer.ats_analyzer import analyze_ats; print(analyze_ats('DevOps Engineer with Jenkins and Docker.', {}))"
```

A deliberately incomplete resume should not receive a high ATS compatibility score.

## 9.2 Remove `None:` recommendation output

File:

```text
backend/analyzer/recommendations.py
```

When an alternative group has no label, do not emit:

```text
None: ...
```

Instead derive a human-readable fallback such as:

```text
Alternative requirement (AWS / Azure)
```

Use `.get()` for optional fields to avoid unnecessary `KeyError`.

Syntax test:

```powershell
python -m py_compile analyzer/recommendations.py
```

## 9.3 Improve required/preferred skill breakdown

The JD result should distinguish:

- required skills;
- preferred skills;
- matched skills;
- not-detected skills;
- alternatives;
- critical gaps.

Do not treat every option in an alternative group as independently mandatory.

Example:

```text
AWS or Azure
```

should not become two required gaps if one option is satisfied.

## 9.4 Improve PDF/DOCX cleanup

File:

```text
backend/analyzer/parser.py
```

Validate dependencies:

```powershell
python -m pip show pypdf
python -m pip show python-docx
```

Install if missing:

```powershell
python -m pip install pypdf python-docx
```

Clean common extraction artifacts generically instead of maintaining resume-specific hard-coded corrections.

## 9.5 Calibrate JD Match scoring

File:

```text
backend/analyzer/scoring.py
```

Design principles:

1. required skills carry more weight than preferred skills;
2. experience uses proportional matching when below the minimum;
3. missing/unknown values use `None` rather than invented success;
4. weights dynamically normalize around available evidence;
5. responsibility/keyword matching measures coverage rather than giving full credit for a single keyword;
6. education is scored only when a reliable requirement is detected;
7. alternatives are handled as groups.

Experience example:

```text
detected experience / required experience
```

with an upper bound of 100%.

## 9.6 Add score explanations

The API should provide human-readable explanations showing why scores were produced.

Examples:

```text
experience_match
role_match
keyword_match_details
score_explanations
```

This makes the analyzer explainable rather than returning unexplained numbers.

## 9.7 Add edge-case and regression tests

Create/maintain tests for:

- experience ranges (`1-3`, `2–4`, `3 to 5`, `4+`, `at least 3`);
- alternative requirements;
- missing experience;
- missing role evidence;
- weak resumes;
- non-IT domains;
- unknown concepts;
- education regex false positives;
- responsibility coverage.

Run syntax checks:

```powershell
python -m py_compile analyzer\*.py
```

Or PowerShell:

```powershell
Get-ChildItem analyzer\*.py | ForEach-Object {
    python -m py_compile $_.FullName
}
```

## 9.8 Generalization principle

The target architecture is:

```text
ANY Resume
    ↓
structured evidence
    ↓
canonicalization
    ↓
matching

ANY JD
    ↓
structured requirements
    ↓
canonicalization
    ↓
matching
```

Do not patch production logic for a single employer, JD, or domain.

---

# PHASE 4 — AZURE COSMOS DB PERSISTENCE

## 10. Phase 4 Objective

Persist analysis history so results can be retrieved later without rerunning the analyzer.

## 10.1 Create Cosmos DB for NoSQL account

First verify Azure:

```powershell
az account show --output table
```

Create the account with free tier if the subscription is eligible:

```powershell
az cosmosdb create `
    --name $COSMOS_ACCOUNT `
    --resource-group $RESOURCE_GROUP `
    --locations regionName=centralindia `
    --enable-free-tier true `
    --default-consistency-level Session
```

Verify:

```powershell
az cosmosdb show `
    --name $COSMOS_ACCOUNT `
    --resource-group $RESOURCE_GROUP `
    --query "{name:name,location:location,provisioningState:provisioningState,enableFreeTier:enableFreeTier}" `
    --output table
```

If a region fails due to capacity, inspect whether Azure left a failed resource object.

Delete failed object before retrying:

```powershell
az cosmosdb delete `
    --name $COSMOS_ACCOUNT `
    --resource-group $RESOURCE_GROUP `
    --yes
```

## 10.2 Define data model

Database:

```text
resume-analyzer-db
```

Container:

```text
analyses
```

Final partition key:

```text
/id
```

Store structured analysis metadata such as:

```text
id
created_at
candidate_name
resume_filename
job_title
resume_score
ats_score
job_match_score
matched_skills
missing_skills
critical_missing_skills
required_skill_breakdown
preferred_skill_breakdown
experience_match
role_match
keyword_match
keyword_match_details
score_explanations
recommendations
```

Do **not** store:

```text
raw PDF/DOCX bytes
Azure AI keys
Cosmos keys
environment variables
passwords
full raw resume text unless a future requirement explicitly needs it
```

## 10.3 Configure Cosmos credentials locally

Retrieve endpoint and key into local PowerShell variables without printing the values:

```powershell
$cosmosEndpoint = az cosmosdb show `
    --name $COSMOS_ACCOUNT `
    --resource-group $RESOURCE_GROUP `
    --query documentEndpoint `
    --output tsv

$cosmosKey = az cosmosdb keys list `
    --name $COSMOS_ACCOUNT `
    --resource-group $RESOURCE_GROUP `
    --type keys `
    --query primaryMasterKey `
    --output tsv
```

Safe verification:

```powershell
Write-Host "Cosmos endpoint loaded:" ([bool]$cosmosEndpoint)
Write-Host "Cosmos key loaded:" ([bool]$cosmosKey)
```

Add to local `.env` manually:

```dotenv
COSMOS_ENDPOINT=<cosmos-endpoint>
COSMOS_KEY=<cosmos-key>
COSMOS_DATABASE=resume-analyzer-db
COSMOS_CONTAINER=analyses
```

Never paste the real values into documentation.

## 10.4 Install SDK

```powershell
python -m pip install azure-cosmos
python -m pip show azure-cosmos
```

Verify imports:

```powershell
python -c "from azure.cosmos import CosmosClient, PartitionKey; print('Cosmos SDK import successful')"
```

Add:

```text
azure-cosmos
```

to `backend/requirements.txt`.

## 10.5 Create database/container setup script

Create:

```text
backend/setup_cosmos.py
```

Use:

```python
client.create_database_if_not_exists(...)
database.create_container_if_not_exists(...)
```

and:

```python
PartitionKey(path="/id")
```

Run from repository root:

```powershell
python backend/setup_cosmos.py
```

Verify database:

```powershell
az cosmosdb sql database show `
    --account-name $COSMOS_ACCOUNT `
    --resource-group $RESOURCE_GROUP `
    --name $COSMOS_DATABASE `
    --output table
```

Verify container:

```powershell
az cosmosdb sql container show `
    --account-name $COSMOS_ACCOUNT `
    --resource-group $RESOURCE_GROUP `
    --database-name $COSMOS_DATABASE `
    --name $COSMOS_CONTAINER `
    --output table
```

## 10.6 Build storage layer

Create:

```text
backend/analyzer/cosmos_storage.py
```

Responsibilities:

```text
get_cosmos_container()
build_analysis_document()
save_analysis()
get_analysis()
get_analysis_history()
```

Generate analysis IDs with UUIDs and timestamps in UTC.

## 10.7 Retrieve one analysis

Because `id` is also the partition key:

```python
container.read_item(
    item=analysis_id,
    partition_key=analysis_id,
)
```

This is a point read.

## 10.8 Retrieve recent history

Use a Cosmos SQL query ordered by `created_at`.

Because `/id` distributes items across partitions, history queries require cross-partition querying.

## 10.9 Integrate persistence into `/api/analyze`

Persistence is secondary to analysis.

Use a safe boundary:

```text
analysis succeeds
→ try to save
→ if Cosmos fails, log it
→ return analysis anyway
```

Do not allow database downtime to destroy the core user result.

Return:

```json
{
  "success": true,
  "analysis_id": "<uuid-or-null>",
  "candidate": {},
  "analysis": {},
  "job_match": {},
  "azure_ai": {}
}
```

## 10.10 Major Phase 4 troubleshooting

### Portal showed unusable/EUAP regions

Use Azure CLI and a valid service region.

### Region creation failed

Inspect provisioning state, delete a failed resource object, then retry in another supported region.

### Storage layer expected wrong score type

Keep contracts consistent. If the API supplies `resume_score` as an integer, persistence code must not call dictionary methods on it.

### Cosmos failure should not break analysis

Wrap document-building and persistence under the same exception boundary and log the internal error.

---

# PHASE 5 — BACKEND / API FINALIZATION

## 11. Phase 5 Objective

Make the Azure Functions API robust, explicit, and production-oriented.

Final routes:

```text
GET  /api/health
POST /api/analyze
```

Main file:

```text
backend/function_app.py
```

## 11.1 Always run Functions from `backend/`

Correct:

```powershell
cd backend
func start
```

Incorrect:

```text
running func start from repository root
```

A wrong working directory can produce:

```text
Can't determine project language from files.
Worker runtime cannot be 'None'.
```

## 11.2 Request validation constants

The project finalized these application limits:

```python
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MIN_JOB_DESCRIPTION_LENGTH = 100
ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".txt"}
```

Meaning:

- maximum resume file size: 5 MB;
- minimum JD length: 100 characters;
- supported extensions: PDF, DOCX, TXT.

## 11.3 Validate request

Validation should reject:

- missing filename;
- empty file;
- file larger than 5 MB;
- unsupported extension;
- missing JD;
- JD shorter than 100 characters;
- malformed JSON;
- JSON body that is not an object.

Use:

```python
extension = Path(filename).suffix.lower()
```

and check against the allowlist.

## 11.4 Handle invalid JSON accurately

Do not silently transform malformed JSON into `{}`.

Use:

```python
try:
    body = req.get_json() or {}
except ValueError as exc:
    raise ValueError("Invalid JSON request body.") from exc
```

Then validate:

```python
if not isinstance(body, dict):
    raise ValueError("JSON request body must be an object.")
```

## 11.5 Standard error shape

Validation error:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "..."
  }
}
```

Unexpected server error:

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Resume analysis failed."
  }
}
```

Do not expose raw exceptions to the user. Log detailed exceptions server-side.

## 11.6 Health endpoint

Route:

```text
GET /api/health
```

Expected conceptual response:

```json
{
  "success": true,
  "service": "AI Resume Analyzer",
  "status": "healthy"
}
```

Local test:

```powershell
Invoke-RestMethod "http://localhost:7071/api/health"
```

## 11.7 Complete local API test

Start:

```powershell
cd backend
func start
```

Then submit a valid request from another terminal or the frontend.

For nested response inspection:

```powershell
$response | ConvertTo-Json -Depth 20
```

Verify:

```text
success = true
analysis_id present or null
analysis.resume_score present
analysis.ats.score present
job_match.match_score present
azure_ai.resume available structure
azure_ai.job_description available structure
```

## 11.8 API troubleshooting

### `func start` cannot detect language

Run from `backend/`.

### `py_compile` cannot find file

Use the correct working directory or full relative path.

### Validation test unexpectedly still returns old error

Rebuild the test request body; PowerShell variables may still contain the previous invalid case.

### PowerShell `Invoke-WebRequest` parser warning

Use `Invoke-RestMethod` where possible, or `-UseBasicParsing` when appropriate.

---

# PHASE 6 — FRONTEND FINAL INTEGRATION

## 12. Phase 6 Objective

Connect the browser UI to the final backend and display all major result categories.

Files:

```text
frontend/index.html
frontend/script.js
frontend/styles.css
```

## 12.1 Send multipart form data

Frontend concept:

```javascript
const formData = new FormData();
formData.append("file", file);
formData.append("job_description", jd);

const response = await fetch("<API_URL>/api/analyze", {
  method: "POST",
  body: formData,
});
```

Do not manually set `Content-Type: multipart/form-data`; the browser must generate the multipart boundary.

## 12.2 Frontend validation

Before submit:

- a resume must be selected;
- JD must be at least 100 characters;
- disable the button while the request is running.

## 12.3 Map API response

Conceptual API:

```json
{
  "success": true,
  "analysis_id": "...",
  "candidate": {},
  "analysis": {},
  "job_match": {},
  "azure_ai": {}
}
```

UI maps:

```text
candidate → candidate name
analysis → resume quality / ATS / skills / experience / strengths / recommendations
job_match → match score / matched skills / not-detected skills / experience / role / keyword / education / recommendations
azure_ai → key phrases / entities
```

## 12.4 Use careful labels

Use:

```text
ATS Compatibility
```

not an absolute claim such as “universal ATS score.”

Use:

```text
JD Skills Not Detected in Resume
```

instead of asserting the candidate does not possess the skill.

Add a note that “not detected” is based on resume evidence.

## 12.5 Azure AI display

Show:

- Resume Key Phrases.
- JD Key Phrases.
- Detected Resume Entities.

Clearly state that NLP insights are supplementary and do not directly determine JD Match.

## 12.6 Loading and error states

During analysis:

```text
button disabled
file input disabled
JD textarea disabled
loader visible
button label = Analyzing...
```

On failure, show a user-readable message.

Only convert actual network/fetch failures into “Unable to connect” messages. Preserve valid API error messages when the server responded.

## 12.7 Common frontend bugs

### `Cannot set properties of null`

Cause: JavaScript references an element ID not present in `index.html`.

Debug:

```javascript
console.log(document.getElementById("targetId"));
```

Fix the HTML/JS ID mismatch.

### Missing ATS element

Ensure the page contains the element expected by `script.js`.

### `sharedPhrases is not defined`

Keep variables within valid scope or remove stale references.

### Wrong fetch URL

Local development:

```text
http://localhost:7071/api/analyze
```

Production:

```text
https://<FUNCTION_APP_HOST>/api/analyze
```

Do not paste Markdown syntax such as:

```text
[https://...](https://...)
```

inside JavaScript.

## 12.8 Run local frontend

From repository root:

```powershell
cd frontend
python -m http.server 5500
```

Open:

```text
http://localhost:5500
```

Run backend separately from `backend/`.

---

# PHASE 7 — AUTOMATED TESTING

## 13. Phase 7 Objective

Convert manual verification into repeatable, offline-capable automated tests suitable for CI/CD.

The suite deliberately avoids live cloud calls during unit/API tests.

## 13.1 Create test package

```powershell
cd "<PROJECT_ROOT>"

New-Item -ItemType Directory -Force backend\tests
New-Item -ItemType File -Force backend\tests\__init__.py
```

Install pytest:

```powershell
python -m pip install pytest
pytest --version
```

Create:

```text
backend/requirements-dev.txt
```

with:

```text
pytest
```

## 13.2 Final test files

```text
test_api.py
test_ats_analyzer.py
test_azure_language.py
test_experience_matching.py
test_jd_analyzer.py
test_recommendations.py
test_regression_generalized.py
test_resume_analyzer.py
test_skill_matching.py
```

## 13.3 Unit tests

Cover:

- JD parsing;
- resume parsing;
- ATS;
- recommendations;
- education patterns;
- experience ranges;
- non-IT skills;
- `None`-safe handling.

## 13.4 Skill matching tests

Cover controlled aliases such as:

```text
KQL ↔ Kusto
Power BI ↔ powerbi
Node.js ↔ nodejs
REST API ↔ RESTful API
```

Also verify negative cases, e.g. Docker must not equal Kubernetes.

A legitimate generic bug found by the tests was the missing `Power BI` ↔ `powerbi` equivalence.

## 13.5 Experience matching tests

Examples:

```text
4 vs 3      → 100
3 vs 3      → 100
2.92 vs 3   → approximately 97
1 vs 4      → 25
missing JD requirement → None
unknown resume experience → None
```

## 13.6 Mock Azure AI

Use `unittest.mock.MagicMock` and `patch`.

Do not call live Azure in unit tests.

Benefits:

```text
fast
repeatable
offline
free
safe for CI
```

## 13.7 API tests

Construct `azure.functions.HttpRequest` directly.

Test:

- `/api/health`;
- empty resume;
- missing/short JD;
- valid request structure;
- Azure integration mocked;
- persistence safely isolated.

## 13.8 Regression tests

The original standalone generalized analyzer script was converted into actual pytest `test_*` functions.

Regression domains include:

- DevOps;
- Finance;
- HR;
- Nursing;
- unknown museum domain;
- alternatives;
- soft-skill measurability;
- missing experience.

## 13.9 Run test suite

From backend:

```powershell
cd backend
python -m pytest tests -v
```

Final result in the completed project:

```text
74 passed
```

Syntax verification:

```powershell
python -m py_compile function_app.py

Get-ChildItem analyzer\*.py | ForEach-Object {
    python -m py_compile $_.FullName
}
```

No output means syntax is clean.

## 13.10 Test troubleshooting

### `collected 0 items`

Check:

```powershell
Get-ChildItem tests
Select-String -Path tests\test_regression_generalized.py -Pattern "^def test_"
```

A file named `test_*.py` is not enough; pytest still needs discoverable `test_*` functions/classes.

### Recommendation wording test fails while production wording is correct

Relax tests to assert the intended behavior, not one exact sentence.

### Experience wording test fails while logic is correct

Update the test expectation, not correct production behavior.

---

# PHASE 8 — AZURE DEPLOYMENT

## 14. Phase 8 Objective

Deploy the tested backend and frontend to Azure and verify Azure AI + Cosmos in production.

## 14.1 Verify Azure session

```powershell
az account show --query "{Name:name,Id:id,TenantId:tenantId,State:state}" --output table
az account list --refresh --output table
```

Verify resource group:

```powershell
az group show --name $RESOURCE_GROUP --output table
```

If login context is stale:

```powershell
az logout
az account clear
az login
```

At the interactive subscription prompt, select the correct subscription before running additional commands.

## 14.2 Register required resource providers

Check Storage:

```powershell
az provider show --namespace Microsoft.Storage --query "registrationState" --output tsv
```

If required:

```powershell
az provider register --namespace Microsoft.Storage
```

Monitor:

```powershell
az provider show --namespace Microsoft.Storage --query "registrationState" --output tsv
```

Check Web:

```powershell
az provider show --namespace Microsoft.Web --query "registrationState" --output tsv
```

If required:

```powershell
az provider register --namespace Microsoft.Web
```

Provider registration itself does not create a paid resource.

## 14.3 Create Function storage account

Check global name:

```powershell
az storage account check-name `
    --name $STORAGE_NAME `
    --query "{Name:name,Available:nameAvailable,Reason:reason}" `
    --output table
```

Create:

```powershell
az storage account create `
    --name $STORAGE_NAME `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION `
    --sku Standard_LRS `
    --allow-blob-public-access false
```

Verify:

```powershell
az storage account show `
    --name $STORAGE_NAME `
    --resource-group $RESOURCE_GROUP `
    --query "{Name:name,Location:primaryLocation,SKU:sku.name,Status:statusOfPrimary}" `
    --output table
```

## 14.4 Create Flex Consumption Function App

```powershell
az functionapp create `
    --resource-group $RESOURCE_GROUP `
    --name $FUNCTION_APP `
    --storage-account $STORAGE_NAME `
    --flexconsumption-location $LOCATION `
    --runtime python `
    --runtime-version 3.10
```

Verify:

```powershell
az functionapp show `
    --name $FUNCTION_APP `
    --resource-group $RESOURCE_GROUP `
    --query "{Name:name,State:state,Host:defaultHostName,Location:location}" `
    --output table
```

Check the returned configuration and ensure no Always Ready instance was intentionally configured if the goal is minimal usage.

## 14.5 Load local `.env` without printing secrets

From repo root:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][A-Za-z0-9_]*)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2].Trim().Trim('"').Trim("'")
        Set-Item -Path "Env:$name" -Value $value
    }
}
```

Verify only presence:

```powershell
@(
    "AZURE_LANGUAGE_ENDPOINT",
    "AZURE_LANGUAGE_KEY",
    "COSMOS_ENDPOINT",
    "COSMOS_KEY",
    "COSMOS_DATABASE",
    "COSMOS_CONTAINER"
) | ForEach-Object {
    $value = [Environment]::GetEnvironmentVariable($_)
    if ($value) { "$_ = LOADED" } else { "$_ = MISSING" }
}
```

## 14.6 Configure production Function App settings

```powershell
az functionapp config appsettings set `
    --name $FUNCTION_APP `
    --resource-group $RESOURCE_GROUP `
    --settings `
    AZURE_LANGUAGE_ENDPOINT="$env:AZURE_LANGUAGE_ENDPOINT" `
    AZURE_LANGUAGE_KEY="$env:AZURE_LANGUAGE_KEY" `
    COSMOS_ENDPOINT="$env:COSMOS_ENDPOINT" `
    COSMOS_KEY="$env:COSMOS_KEY" `
    COSMOS_DATABASE="$env:COSMOS_DATABASE" `
    COSMOS_CONTAINER="$env:COSMOS_CONTAINER"
```

Verify names only:

```powershell
az functionapp config appsettings list `
    --name $FUNCTION_APP `
    --resource-group $RESOURCE_GROUP `
    --query "[?name=='AZURE_LANGUAGE_ENDPOINT' || name=='AZURE_LANGUAGE_KEY' || name=='COSMOS_ENDPOINT' || name=='COSMOS_KEY' || name=='COSMOS_DATABASE' || name=='COSMOS_CONTAINER'].name" `
    --output table
```

## 14.7 Deploy backend manually for first production verification

```powershell
cd backend
func azure functionapp publish $FUNCTION_APP
```

Test health:

```powershell
$FUNCTION_HOST = az functionapp show `
    --name $FUNCTION_APP `
    --resource-group $RESOURCE_GROUP `
    --query defaultHostName `
    --output tsv

Invoke-RestMethod "https://$FUNCTION_HOST/api/health"
```

## 14.8 Configure CORS for local frontend

```powershell
az functionapp cors add `
    --name $FUNCTION_APP `
    --resource-group $RESOURCE_GROUP `
    --allowed-origins http://localhost:5500
```

Verify:

```powershell
az functionapp cors show `
    --name $FUNCTION_APP `
    --resource-group $RESOURCE_GROUP `
    --output json
```

### PowerShell backtick warning

Do not write:

```text
`az ...
```

The backtick is only a line-continuation character at line ends.

## 14.9 Create Azure Static Web App

From repo root:

```powershell
az staticwebapp create `
    --name $STATIC_WEB_APP `
    --resource-group $RESOURCE_GROUP `
    --location $STATIC_LOCATION `
    --sku Free
```

Retrieve hostname without hard-coding it:

```powershell
$SWA_HOST = az staticwebapp show `
    --name $STATIC_WEB_APP `
    --resource-group $RESOURCE_GROUP `
    --query defaultHostname `
    --output tsv
```

## 14.10 Retrieve SWA deployment token for manual deployment

```powershell
$SWA_TOKEN = az staticwebapp secrets list `
    --name $STATIC_WEB_APP `
    --resource-group $RESOURCE_GROUP `
    --query "properties.apiKey" `
    --output tsv
```

Verify only existence:

```powershell
if ($SWA_TOKEN) { "SWA deployment token loaded" } else { "Token missing" }
```

Never print or commit the token.

## 14.11 Deploy frontend

```powershell
npx @azure/static-web-apps-cli@latest deploy ./frontend `
    --deployment-token "$SWA_TOKEN" `
    --env prod
```

## 14.12 Configure live frontend CORS

```powershell
az functionapp cors add `
    --name $FUNCTION_APP `
    --resource-group $RESOURCE_GROUP `
    --allowed-origins "https://$SWA_HOST"
```

Verify CORS again.

## 14.13 Update frontend production API URL

In `frontend/script.js`, production `fetch()` must point to:

```javascript
fetch("https://<FUNCTION_APP_HOST>/api/analyze", {
    method: "POST",
    body: formData,
});
```

Do not accidentally paste Markdown link syntax into JavaScript.

Redeploy the frontend after editing.

Hard refresh browser:

```text
Ctrl + Shift + R
```

## 14.14 End-to-end production test

On the deployed Static Web App:

1. upload a valid PDF/DOCX/TXT resume;
2. paste a JD longer than 100 characters;
3. submit;
4. verify Resume Quality;
5. verify ATS Compatibility;
6. verify JD Match;
7. verify matched/not-detected skills;
8. verify experience/role/keyword/education;
9. verify Azure AI key phrases/entities;
10. verify no raw internal exception is visible.

## 14.15 Verify Cosmos persistence

Azure Portal:

```text
Cosmos DB
→ Data Explorer
→ resume-analyzer-db
→ analyses
→ Items
```

Open the newest analysis and confirm it corresponds to the production request.

Do not capture credentials in the screenshot.

## 14.16 Phase 8 troubleshooting

### `SubscriptionNotFound` only on Storage commands

Check:

```powershell
az provider show --namespace Microsoft.Storage --query "registrationState" --output tsv
```

Register if needed.

### Function creation says `Microsoft.Web` not registered

Register:

```powershell
az provider register --namespace Microsoft.Web
```

### Frontend POST returns 405 against Static Web App root

Use browser DevTools → Network. Confirm the request is sent to Function `/api/analyze`, not `/`.

### SWA CLI generic `StaticSitesClient` failure

Run:

```powershell
npx @azure/static-web-apps-cli@latest deploy ./frontend `
    --deployment-token "$SWA_TOKEN" `
    --env production `
    --verbose silly
```

Read the first real diagnostic. In this project, the useful message was an invalid deployment token rather than the generic native-binary warning.

Refresh token and use the working environment form:

```powershell
npx @azure/static-web-apps-cli@latest deploy ./frontend `
    --deployment-token "$SWA_TOKEN" `
    --env prod
```

---

# PHASE 9 — CI/CD WITH GITHUB ACTIONS

## 15. Phase 9 Objective

Automate testing and backend deployment.

Desired flow:

```text
push to main
→ tests
→ if tests fail: stop
→ if tests pass: OIDC login
→ deploy backend
```

## 15.1 Create workflow directory

```powershell
New-Item -ItemType Directory -Force ".github\workflows"
```

Create:

```text
.github/workflows/ci-cd.yml
```

## 15.2 Recommended final workflow

Use a production-safe condition so pull requests run tests but do not deploy.

```yaml
name: AI Resume Analyzer CI/CD

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  test-backend:
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: backend

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run syntax checks
        run: |
          python -m py_compile function_app.py
          python -m compileall analyzer

      - name: Run automated tests
        run: |
          python -m pytest tests -v

  deploy-backend:
    needs: test-backend
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    permissions:
      id-token: write
      contents: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Login to Azure with OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy Azure Function App
        uses: Azure/functions-action@v1
        with:
          app-name: ai-resume-analyzer-api-ps
          package: backend
          sku: flexconsumption
          remote-build: true
```

The project initially implemented the same test/deploy design without the explicit deploy `if:` line; the line above is the recommended final hardening so PRs do not attempt production deployment.

## 15.3 Commit initial CI workflow

```powershell
git add .github\workflows\ci-cd.yml
git status
git commit -m "Add GitHub Actions CI workflow"
git push origin main
```

## 15.4 GitHub PAT workflow-scope issue

If GitHub rejects the push because a classic PAT cannot modify `.github/workflows/`, create/use a PAT with the necessary repository and workflow permissions.

If Windows continues using the old token:

```powershell
echo "protocol=https`nhost=github.com" | git credential-manager erase
git push origin main
```

Never put the PAT into the remote URL, source code, or SOP.

## 15.5 Verify automated tests

GitHub:

```text
Repository
→ Actions
→ AI Resume Analyzer CI/CD
→ test-backend
```

Expected:

```text
Checkout repository
Set up Python
Install dependencies
Run syntax checks
Run automated tests
```

Final suite:

```text
74 passed
```

## 15.6 Flex Consumption publish-profile limitation

The attempted publishing-profile command was unsupported for this Flex Consumption setup.

Use OIDC instead.

Final trust architecture:

```text
GitHub Actions
→ OIDC token
→ Azure federated credential
→ user-assigned managed identity
→ RBAC
→ Function App
```

## 15.7 Create user-assigned managed identity

```powershell
az identity create `
    --name gha-ai-resume-analyzer `
    --resource-group $RESOURCE_GROUP `
    --location $LOCATION
```

Capture the returned identifiers privately:

```text
clientId
principalId
tenantId
```

Do not place the actual values in public documentation.

## 15.8 Assign Function-scoped RBAC

Get Function resource ID:

```powershell
$FUNCTION_APP_ID = az functionapp show `
    --name $FUNCTION_APP `
    --resource-group $RESOURCE_GROUP `
    --query id `
    --output tsv
```

Set the principal ID privately:

```powershell
$IDENTITY_PRINCIPAL = "<MANAGED_IDENTITY_PRINCIPAL_ID>"
```

Assign:

```powershell
az role assignment create `
    --assignee $IDENTITY_PRINCIPAL `
    --role "Website Contributor" `
    --scope $FUNCTION_APP_ID
```

This scopes deployment permission to the Function App instead of the whole subscription.

## 15.9 Create federated credential

GitHub OIDC subject formats may evolve. **Use the exact subject shown by the GitHub Actions OIDC failure/log or GitHub’s current documented subject format.**

Example pattern:

```powershell
az identity federated-credential create `
    --identity-name gha-ai-resume-analyzer `
    --resource-group $RESOURCE_GROUP `
    --name github-main-deploy `
    --issuer https://token.actions.githubusercontent.com `
    --subject "<EXACT_GITHUB_OIDC_SUBJECT_FOR_MAIN>" `
    --audiences api://AzureADTokenExchange
```

If the subject is wrong, Azure login fails with a “no matching federated identity record” error.

To replace a wrong credential:

```powershell
az identity federated-credential delete `
    --identity-name gha-ai-resume-analyzer `
    --resource-group $RESOURCE_GROUP `
    --name github-main-deploy `
    --yes
```

Then recreate it with the exact presented subject.

## 15.10 GitHub repository secrets

GitHub:

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
```

Create names only:

```text
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
```

Use actual values in GitHub UI, but never include them in public documentation.

No Azure client secret is required for OIDC.

## 15.11 Commit OIDC workflow

```powershell
git add .github\workflows\ci-cd.yml
git commit -m "Add OIDC backend deployment workflow"
git push origin main
```

Expected successful deploy logs include concepts such as:

```text
RBAC authentication
FlexConsumption detected
remote-build true
One Deploy
Successfully deployed web package
```

## 15.12 Intentional failure test

Create a temporary failing test:

```powershell
@'
def test_pipeline_failure_demo():
    assert False, "Intentional CI/CD failure test"
'@ | Set-Content "backend\tests\test_pipeline_failure_demo.py"
```

Commit/push:

```powershell
git add backend\tests\test_pipeline_failure_demo.py
git commit -m "Test CI failure handling"
git push origin main
```

Expected:

```text
test-backend FAILED
deploy-backend SKIPPED
```

This proves the deployment gate works.

## 15.13 Restore successful pipeline

Remove temporary test:

```powershell
Remove-Item "backend\tests\test_pipeline_failure_demo.py"
```

Commit/push:

```powershell
git add -u
git commit -m "Restore successful CI pipeline"
git push origin main
```

Expected:

```text
test-backend PASSED
deploy-backend PASSED
```

## 15.14 Phase 9 troubleshooting

### PAT lacks workflow permission

Use an appropriately scoped token, then clear cached credentials if required.

### YAML indentation

`test-backend` and `deploy-backend` must be siblings under `jobs:`.

### Publish profile unavailable on Flex

Use OIDC.

### OIDC `AADSTS700213`

Compare issuer, audience, and especially subject. Azure matching is exact.

### Node deprecation warning

A warning is not a failure if the action completes successfully. Do not force an old insecure Node runtime solely to suppress a warning.

---

# PHASE 10 — SECURITY AND PRODUCTION CLEANUP

## 16. Phase 10 Objective

Perform a final security review before publishing documentation and treating the repository as portfolio-ready.

## 16.1 Verify no secret files were committed

From repo root:

```powershell
git log --all --full-history --oneline -- .env
```

```powershell
git log --all --full-history --oneline -- backend/.env backend/local.settings.json
```

No output means those file paths were not committed.

## 16.2 Search history for secret variable names

```powershell
$patterns = @(
    "AZURE_LANGUAGE_KEY",
    "COSMOS_KEY",
    "DEPLOYMENT_TOKEN",
    "SWA_TOKEN",
    "AZURE_FUNCTIONAPP_PUBLISH_PROFILE",
    "clientSecret"
)

foreach ($pattern in $patterns) {
    $result = git log --all -S"$pattern" --oneline
    if ($result) {
        Write-Host "$pattern : FOUND IN HISTORY"
    } else {
        Write-Host "$pattern : NOT FOUND"
    }
}
```

Finding a variable **name** is normal because source code may call `os.getenv("COSMOS_KEY")`.

## 16.3 Search for the actual currently loaded key values without printing them

Load `.env`:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][A-Za-z0-9_]*)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2].Trim().Trim('"').Trim("'")
        Set-Item -Path "Env:$name" -Value $value
    }
}
```

Azure Language key:

```powershell
if ($env:AZURE_LANGUAGE_KEY) {
    $result = git log --all -S"$env:AZURE_LANGUAGE_KEY" --oneline
    if ($result) {
        Write-Host "AZURE_LANGUAGE_KEY VALUE: FOUND IN GIT HISTORY"
    } else {
        Write-Host "AZURE_LANGUAGE_KEY VALUE: NOT FOUND"
    }
} else {
    Write-Host "AZURE_LANGUAGE_KEY: NOT LOADED"
}
```

Cosmos key:

```powershell
if ($env:COSMOS_KEY) {
    $result = git log --all -S"$env:COSMOS_KEY" --oneline
    if ($result) {
        Write-Host "COSMOS_KEY VALUE: FOUND IN GIT HISTORY"
    } else {
        Write-Host "COSMOS_KEY VALUE: NOT FOUND"
    }
} else {
    Write-Host "COSMOS_KEY: NOT LOADED"
}
```

Expected safe result:

```text
AZURE_LANGUAGE_KEY VALUE: NOT FOUND
COSMOS_KEY VALUE: NOT FOUND
```

If a real secret value is found:

1. rotate/revoke the secret immediately;
2. remove it from Git history;
3. force-push only after carefully coordinating the rewrite;
4. update Azure/GitHub configuration with the new value.

## 16.4 Standard `.gitignore`

Recommended:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo

# Virtual environments
.venv/
venv/

# Azure Functions local settings
local.settings.json

# Environment variables / secrets
.env
.env.*

# VS Code
.vscode/

# Logs
*.log

# Testing / coverage
.pytest_cache/
.coverage
.mypy_cache/
.ruff_cache/

# Temporary files
*.tmp
*.temp

# OS files
.DS_Store
Thumbs.db

# Local analysis/output artifacts
analysis-result.json

# Local backup / experimental folders
backend-before-generalization/
generalized-update/
generalized-hotfix/

# Archives
*.zip

# Rough/source documentation that must not be public
docs/documents/
docs/Screenshots/
docs/rough/
docs/private/

# Optional raw screenshot staging
docs/final-screenshots/raw/
```

Do not ignore the final public documentation itself:

```text
docs/SOP.md
docs/architecture.md
docs/final-screenshots/
```

Verify ignores:

```powershell
git check-ignore -v .env backend/local.settings.json .venv
```

## 16.5 Validate uploaded files — final hardening procedure

The project already validates extension and size. For stronger production cleanup, validate both filename/extension **and** content signature.

### Existing allowlist

```python
ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
```

### Recommended filename normalization

Use:

```python
safe_name = Path(filename).name
```

Reject empty/null-byte names:

```python
if "\x00" in filename:
    raise ValueError("Invalid resume filename.")
```

### Recommended signature checks

For a PDF:

```python
file_bytes.startswith(b"%PDF-")
```

For DOCX, remember a DOCX is a ZIP package; check ZIP signature and then parse safely with `python-docx`.

For TXT, decode using a controlled encoding path and reject undecodable/binary-like input.

Do not trust only `Content-Type` from the browser; it is client-controlled metadata.

### Recommended parser rule

Never execute uploaded content. Treat it only as data.

## 16.6 File-size/type limits

Keep:

```text
5 MB maximum
PDF / DOCX / TXT only
```

Test:

- 0-byte file;
- 1-byte fake PDF;
- >5 MB file;
- `.exe`;
- `.pdf` filename with non-PDF bytes;
- uppercase extension (`.PDF`) should normalize correctly;
- filename with path segments;
- filename containing null byte should fail.

## 16.7 Sanitize and validate JD input

Existing minimum:

```text
100 characters
```

Recommended cleanup:

```python
jd = job_description.strip()
```

Reject:

```text
empty
too short
wrong type
extremely large payload if an upper bound is added
```

The analyzer treats text as text; do not evaluate or execute user-supplied strings.

For rendered frontend output, use `textContent`, not unsafe direct HTML insertion for untrusted values.

## 16.8 Review error handling

Validation errors:

```text
HTTP 400
code = VALIDATION_ERROR
safe user-readable message
```

Unexpected server errors:

```text
HTTP 500
code = INTERNAL_ERROR
generic client message
detailed exception only in server logs
```

Never return:

- stack traces;
- filesystem paths;
- connection strings;
- keys;
- tokens;
- raw SDK error objects that may contain infrastructure details.

External dependencies should fail gracefully where appropriate:

```text
Azure AI fails → deterministic analysis can still return
Cosmos fails → analysis can still return, persistence ID may be null
```

## 16.9 Production cleanup test matrix

Before final release, test:

```text
[ ] Valid PDF
[ ] Valid DOCX
[ ] Valid TXT
[ ] Empty file rejected
[ ] Oversized file rejected
[ ] Unsupported extension rejected
[ ] Fake PDF signature rejected (after signature hardening)
[ ] Missing JD rejected
[ ] Short JD rejected
[ ] Invalid JSON rejected
[ ] Azure AI failure handled safely
[ ] Cosmos failure handled safely
[ ] Generic HTTP 500 does not expose exception details
[ ] CORS contains only intended origins
[ ] .env ignored
[ ] local.settings.json ignored
[ ] actual key values not present in Git history
[ ] public screenshots contain no secrets
[ ] public SOP contains no credentials
```

---

# 17. SAFE PUBLIC DOCUMENTATION STRUCTURE

Use:

```text
docs/
├── SOP.md
├── architecture.md
└── final-screenshots/
```

Keep private/rough material ignored:

```text
docs/documents/
docs/Screenshots/
docs/rough/
docs/private/
```

Recommended safe screenshot types:

```text
full_test_suite_74_passed.png
github_actions_tests_passed.png
github_actions_backend_deploy.png
failed_and_recovered_pipeline.png
function_app_created.png
analysis_results.png
azure_ai_insights.png
cosmos_record.png
```

Do **not** publish screenshots containing:

```text
Keys and Endpoint values
Cosmos keys
PATs
deployment tokens
connection strings
.env content
publishing profiles
authorization headers
```

---

# 18. MASTER TROUBLESHOOTING MATRIX

| Symptom | Root cause | Correct action |
|---|---|---|
| `pip` not recognized | shell/path mismatch | use `python -m pip` |
| `ModuleNotFoundError: analyzer` | wrong working directory/import context | run from `backend` or use correct module path |
| `func start` cannot determine language | started from repo root | `cd backend` then `func start` |
| `py_compile` cannot find analyzer/file | wrong directory | use `cd backend` or full path |
| Weak resume gets unrealistic ATS score | subtractive score model | additive earned-score model |
| `None:` appears in recommendation | optional label not checked | fallback label + `.get()` |
| Scoring edit causes `IndentationError` | malformed block indentation | compile module and fix structure |
| Cosmos region deployment fails | capacity/region availability | inspect failed resource, delete, retry supported region |
| Cosmos persistence crashes on score | type contract mismatch | align storage with API data types |
| API invalid JSON looks like missing data | exception swallowed | raise explicit invalid JSON validation error |
| Frontend `Cannot set properties of null` | DOM ID mismatch | align HTML IDs and JS selectors |
| Static frontend POST returns 405 | request sent to SWA root | use Function `/api/analyze` URL |
| SWA generic binary error | wrapper message hid root cause | rerun with `--verbose silly` |
| SWA deployment token invalid | stale/rejected token | retrieve fresh token; never print it |
| `SubscriptionNotFound` on Storage only | Storage provider not registered | register `Microsoft.Storage` |
| Function creation missing registration | `Microsoft.Web` not registered | register `Microsoft.Web` |
| PowerShell `z is not recognized` | command started with stray backtick | remove leading backtick |
| Git rejects workflow push | PAT lacks workflow permission | use correct permission and reauthenticate |
| New PAT still ignored | old credential cached | `git credential-manager erase` |
| GitHub YAML deploy job malformed | indentation | make jobs siblings under `jobs:` |
| Flex publish profile unsupported | plan limitation | use OIDC |
| OIDC `AADSTS700213` | federated subject mismatch | use exact GitHub subject |
| pytest `collected 0 items` | discovery/file/function naming | ensure `test_*.py` + `test_*` functions |
| test wording fails, production is correct | overly strict assertion | test behavior, not one exact sentence |
| CI test fails | intentional/real regression | deploy job must remain skipped |
| Node deprecation warning | action runner warning | upgrade action when needed; do not force insecure runtime |

---

# 19. FINAL VALIDATION CHECKLIST

## Local

```text
[ ] virtual environment active
[ ] runtime dependencies installed
[ ] dev dependencies installed
[ ] backend starts from backend/
[ ] /api/health = healthy
[ ] valid /api/analyze works
[ ] invalid requests return structured 400
[ ] 74 tests pass
[ ] syntax checks pass
```

Run:

```powershell
cd backend
python -m pytest tests -v
python -m py_compile function_app.py

Get-ChildItem analyzer\*.py | ForEach-Object {
    python -m py_compile $_.FullName
}
```

## Production

```text
[ ] Function App Running
[ ] Flex Consumption configured
[ ] application settings exist
[ ] live /api/health works
[ ] CORS local origin configured only if still needed
[ ] CORS live frontend origin configured
[ ] Static Web App loads
[ ] frontend posts to Function /api/analyze
[ ] real analysis completes
[ ] Azure AI section returns safely
[ ] Cosmos contains the corresponding analysis record
```

## CI/CD

```text
[ ] push to main triggers workflow
[ ] tests run automatically
[ ] failed tests prevent deploy
[ ] successful tests allow deploy
[ ] OIDC login succeeds
[ ] backend deployment succeeds
[ ] no Azure client secret stored
```

## Security

```text
[ ] .env not tracked
[ ] local.settings.json not tracked
[ ] actual key values not found in Git history
[ ] public docs/screenshots have no secrets
[ ] uploaded file validation enabled
[ ] 5 MB size limit enabled
[ ] PDF/DOCX/TXT allowlist enabled
[ ] safe 400/500 error responses
```

---

# 20. DAILY DEVELOPMENT / RELEASE PROCEDURE

For a normal code change:

```powershell
git status
```

Run tests:

```powershell
cd backend
python -m pytest tests -v
```

Return root:

```powershell
cd ..
```

Review changed files:

```powershell
git diff
git status
```

Stage only intended files:

```powershell
git add <files>
```

Commit:

```powershell
git commit -m "<clear message>"
```

Push:

```powershell
git push origin main
```

Then:

```text
GitHub Actions
→ test-backend
→ deploy-backend
```

Do not manually deploy production after a failed CI run.

---

# 21. NEW-DEVELOPER QUICK START

Assuming Azure resources already exist:

```powershell
git clone https://github.com/<GITHUB_USER>/azure-ai-resume-analyzer.git
cd azure-ai-resume-analyzer

py -3.10 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
python -m pip install -r backend\requirements-dev.txt
```

Create local `.env` privately:

```dotenv
AZURE_LANGUAGE_ENDPOINT=<value>
AZURE_LANGUAGE_KEY=<value>
COSMOS_ENDPOINT=<value>
COSMOS_KEY=<value>
COSMOS_DATABASE=resume-analyzer-db
COSMOS_CONTAINER=analyses
```

Verify `.env` ignored:

```powershell
git check-ignore -v .env
```

Run tests:

```powershell
cd backend
python -m pytest tests -v
```

Run API:

```powershell
func start
```

In another terminal run frontend:

```powershell
cd frontend
python -m http.server 5500
```

Open:

```text
http://localhost:5500
```

---

# 22. ARCHITECTURE DECISIONS TO REMEMBER

1. **Deterministic analyzer controls scoring.** Azure AI Language is enrichment.
2. **ATS Compatibility and JD Match are different measures.**
3. **Unknown evidence stays unknown.** Do not invent a pass.
4. **Alternatives are groups.** `AWS or Azure` is not two mandatory requirements.
5. **Cosmos persistence degrades gracefully.**
6. **Azure AI failure degrades gracefully.**
7. **Frontend uses `textContent` for user-derived text.**
8. **Secrets stay outside Git.**
9. **CI must pass before CD runs.**
10. **OIDC avoids long-lived Azure deployment secrets.**
11. **Production deployment permission is scoped to the Function App.**
12. **Public documentation is sanitized separately from raw project notes.**

---

# 23. RECOMMENDED PUBLIC REPOSITORY DOCUMENTS

After the final security review, publish:

```text
README.md
docs/SOP.md
docs/architecture.md
docs/final-screenshots/
```

Do not publish the raw phase working notes if they may contain account-specific identifiers or screenshots captured during key-management steps.

---

# 24. FINAL COMPLETION CRITERIA

The project is considered operationally complete when all of the following are true:

```text
Core deterministic analyzer                    PASS
Azure AI Language integration                  PASS
Scoring/generalization/explainability           PASS
Cosmos DB persistence                           PASS
API validation/error handling                   PASS
Frontend integration                            PASS
Automated tests                                 PASS
Azure backend/frontend deployment               PASS
CI/CD with OIDC                                 PASS
Failure/recovery pipeline test                  PASS
Git secret-history check                        PASS
.gitignore review                               PASS
File upload hardening review                    PASS
Input sanitization review                       PASS
Error handling security review                  PASS
Public SOP/screenshot credential review         PASS
```

---

# 25. SECURITY-SAFE DOCUMENTATION NOTE

This master SOP intentionally uses placeholders instead of account-specific credential material. If a command returns a key, token, publishing profile, authorization value, tenant/subscription/client/principal identifier, or connection string, keep that value in the local terminal/Azure/GitHub configuration only.

Before committing this SOP:

```powershell
git diff -- docs/SOP.md
```

Search the SOP for suspicious terms:

```powershell
Select-String -Path docs\SOP.md -Pattern "KEY=|TOKEN=|primaryMasterKey|clientSecret|DefaultEndpointsProtocol|AccountKey=" -CaseSensitive:$false
```

Review every match manually.

Finally:

```powershell
git status
```

Stage only the sanitized document and approved screenshots.

---

**End of SOP**
