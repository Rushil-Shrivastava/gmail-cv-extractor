# Gmail CV Extractor — README

A production-ready Gmail → resume ingestion tool that downloads attachments from Gmail, parses resume fields (name, email, phone, skills, experience), deduplicates, stores into a local database, and exports an Excel (data/candidates.xlsx). Runs locally or in Docker / Docker Compose.

This README assumes you do not include any credentials in the repo (good). It tells you exactly what to create and run after cloning.

⸻

Table of contents
1.	Prerequisites
2.	Quick repo layout
3.	Prepare Google credentials (step-by-step)
4.	Local setup (Python 3.12 recommended)
5.	First OAuth run (generate token.pickle)
6.	Run the sync locally
7.	Run the FastAPI server
8.	Docker & Docker Compose usage
9.	Testing (send yourself sample resumes)
10.	Troubleshooting (common errors & fixes)
11.	Security notes & production tips
12.	Optional improvements

⸻

1) Prerequisites
	-	macOS / Linux / Windows with:
	-	Python 3.12 (strongly recommended). (If you already have 3.14, create a 3.12 venv.)
	-	git
	-	pip
	-	(Optional) Docker & Docker Compose if you want to run containers.
	-	(Optional for OCR) Tesseract binary if you plan to OCR scanned PDFs:
	-	macOS (Homebrew): brew install tesseract
	-	Ubuntu/Debian: sudo apt install tesseract-ocr

⸻

2) Quick repo layout (expected)

        gmail-cv-extractor/
        ├── app/
        │   ├── main.py
        │   ├── run_sync.py
        │   ├── parser.py
        │   ├── db.py
        │   └── gmail_client.py
        ├── data/            # created by you
        ├── attachments/     # created by you
        ├── requirements.txt
        ├── Dockerfile
        ├── docker-compose.yml
        └── README.md

Create directories:

    mkdir -p data attachments
    chmod -R 755 data attachments

⸻

3) Prepare Google credentials (detailed)
	1.	Open Google Cloud Console: https://console.cloud.google.com/ and sign in.
	2.	Create/select a project:
	-	Top-left → Project dropdown → New Project → name it (e.g., gmail-cv-extractor).
	3.	Enable Gmail API:
	-	APIs & Services → Library → search Gmail API → Enable.
	4.	Configure OAuth consent screen:
	-	APIs & Services → OAuth consent screen.
	-	Choose External (typical) → Create.
	-	Fill App name, support email, developer contact email.
	-	Scopes: click Add or Remove Scopes and ensure Gmail scopes include https://mail.google.com/ (we recommend full gmail access for reliable attachments).
	-	Test users: add your Gmail address (required for unverified apps).
	5.	Create OAuth credentials:
	-	APIs & Services → Credentials → Create Credentials → OAuth client ID.
	-	Select Application type: Desktop app and create.
	-	Download JSON → save as credentials.json at repo root (do not commit it).
	6.	Add credentials.json to .gitignore (if not already).

⸻

4) Local setup (virtual environment, deps)
	1.	Use Python 3.12 (install via Homebrew on macOS if needed):

        brew install python@3.12
        python3.12 -m venv .venv
        source .venv/bin/activate

	2.	Save the repo requirements.txt (the project includes a recommended one). Example lightweight (spaCy-free) requirements are included in the repo.
	3.	Install dependencies:

        pip install --upgrade pip setuptools wheel
        pip install -r requirements.txt

	4.	(Optional) Install the tesseract binary if you plan to OCR:

# macOS
brew install tesseract


⸻

5) First OAuth run — generate token.pickle
	1.	Place credentials.json in repo root.
	2.	Run initial sync (local machine; this opens a browser to authorize):

        python -m app.run_sync

	3.	A browser window opens → choose your test Google account (the one you added as a test user) → Accept permissions.
	4.	After successful consent, token.pickle is created in your repo. Keep it secure.

If running on a headless server: run this step locally then copy token.pickle into the server or container.

⸻

6) Run the sync locally

After token.pickle exists, run:

    python -m app.run_sync

What the script does:
-	Authenticates via token.pickle / credentials.json.
-	Downloads attachments that match your configured query (filename:resume OR filename:cv and allowed extensions).
-	Parses attachments (regex/fuzzy heuristics), deduplicates by email, inserts candidates into the DB, and exports data/candidates.xlsx.

Summary will be printed to console.

⸻

7) Run FastAPI server (browse candidates)

Start API:

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Open:
-	Swagger UI: http://localhost:8000/docs
-	Endpoints:
-	GET /candidates — list candidates
-	GET /candidate/{id} — candidate detail
-	POST /sync — trigger sync (runs synchronously in current code)

⸻

8) Docker & Docker Compose

Dockerfile (provided)

Basic flow:

    docker build -t gmail-cv-extractor .

Docker run (sync mode)

Mount credentials and token and bind folders:

    docker run --rm \
    -v $(pwd)/credentials.json:/app/credentials.json:ro \
    -v $(pwd)/token.pickle:/app/token.pickle:rw \
    -v $(pwd)/attachments:/app/attachments \
    -v $(pwd)/data:/app/data \
    gmail-cv-extractor

docker-compose (recommended)

Use the docker-compose.yml in the repo. Example use:

    docker compose build
    docker compose up        # default MODE=sync
    MODE=api docker compose up  # run FastAPI

If docker command is missing on macOS, install Docker Desktop: https://www.docker.com/products/docker-desktop/

⸻

9) Testing: create dummy resumes

Option A — send yourself real emails
-	From any email, send to your Gmail with attachments named:
-	John_Resume.pdf, My_CV.docx, Resume_Rushil.txt
-	Run python -m app.run_sync — attachments will be downloaded and parsed.

Option B — mock attachments locally
-	Place files in attachments/ folder:
-	attachments/John_Resume.txt with content:
        Name: John Doe
        Email: john@example.com
        Phone: +91 99999 99999
        Skills: Python, SQL, Docker
-	In run_sync.py temporarily replace attachments = fetch_attachments(...) with:
        attachments = [{"filename":"John_Resume.txt","path":"attachments/John_Resume.txt"}]
-	Run sync to test parser and DB logic.

⸻

10) Troubleshooting (common issues)

- **pg_config executable not found when installing psycopg2:**  
  If you plan to use PostgreSQL, install `libpq-dev` (Linux) or `brew install postgresql` (macOS).  
  If you use SQLite only, remove `psycopg2-binary` from `requirements.txt`.

- **blis/spacy build errors on Python 3.14:**  
  Use Python 3.12 (recommended) or remove spaCy from requirements if you don’t need it.

- **sqlite3.OperationalError: unable to open database file:**  
  Ensure `data/` directory exists and is writable:  
    ```bash
    mkdir -p data attachments
    chmod -R 755 data attachments
    ```

	- **`PDFPasswordIncorrect` when parsing a PDF:**  
  The parser will skip locked PDFs and log a warning.  
  You can inspect the `attachments/` directory to see which files were skipped.

- **`UNIQUE constraint failed: candidates.email`:**  
  Duplicate prevention is handled internally, but if you still see this,  
  ensure `add_candidate()` checks for existing emails before inserting new entries.

- **OAuth flow fails (browser not opening):**  
  Copy the URL printed in the terminal and open it manually in your browser.  
  Make sure the account you choose is added as a **Test User** in your OAuth consent screen.

---

### 🔐 Security Notes & Best Practices

- Never commit `credentials.json` or `token.pickle` to the repository — add them to `.gitignore`.  
- Use secret management solutions in production (e.g. **Vault**, **AWS Secrets Manager**, or **GitHub Secrets**).  
- Limit Gmail API scope if possible (`gmail.readonly`),  
  though attachments access typically requires `https://mail.google.com/`.  
- On shared servers or CI systems, avoid interactive OAuth flows —  
  generate `token.pickle` locally and mount it inside the container.

---

### 🚀 Optional Improvements (Next Steps)

- Add **Alembic migrations** for database schema changes.  
- Replace **SQLite** with **PostgreSQL** for multi-user or production environments.  
- Add a background worker (**Celery** or **RQ**) for heavy parsing jobs.  
- Create a **React UI** for browsing resumes and exporting data.  
- Integrate a **managed resume parser API** or fine-tuned **NER model** for higher parsing accuracy.  
- Add **S3/GCS storage** for attachments and automatic S3 export backups for Excel files.

⸻

# Quick copy-paste checklist (do this right after cloning)

clone
    git clone <your-repo-url>
    cd gmail-cv-extractor

prepare dirs
    mkdir -p data attachments
    chmod -R 755 data attachments

create python venv (python3.12)
    python3.12 -m venv .venv
    source .venv/bin/activate

install deps
    pip install --upgrade pip
    pip install -r requirements.txt

copy credentials.json (create in Google Cloud as explained above)
run this locally to create token.pickle (opens browser)
    python -m app.run_sync

run API (optional)
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

or run in docker-compose
    docker compose build
    docker compose up


⸻